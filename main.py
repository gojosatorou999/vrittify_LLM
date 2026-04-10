"""
FastAPI wrapper for llama.cpp server.
Provides /health, /generate, and /chat endpoints with response time tracking.
"""

import time
import logging
import os
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ─── Configuration ───────────────────────────────────────────────────────────

LLAMA_CPP_BASE_URL = os.environ.get("LLAMA_CPP_URL", "http://localhost:8080")
RESPONSE_TIME_WARN_MS = 5000
REQUEST_TIMEOUT_S = 60

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("llm-api")

# ─── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Local LLM API",
    description=(
        "FastAPI wrapper around a local llama.cpp server running Phi-3 Mini. "
        "Provides simplified /generate and /chat endpoints with response-time tracking."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request / Response Models ───────────────────────────────────────────────


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="The text prompt to send to the model")
    max_tokens: int = Field(default=256, ge=1, le=4096, description="Max tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")


class GenerateResponse(BaseModel):
    text: str
    model: str = "phi-3-mini"
    tokens_generated: int
    response_time_ms: float


class ChatMessage(BaseModel):
    role: str = Field(..., description="One of: system, user, assistant")
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = Field(default=256, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    message: ChatMessage
    model: str = "phi-3-mini"
    tokens_generated: int
    response_time_ms: float


class HealthResponse(BaseModel):
    status: str
    llama_cpp_url: str
    llama_cpp_status: str
    model_loaded: bool


# ─── Helper: call llama.cpp ──────────────────────────────────────────────────

async def _call_llama_chat(
    messages: list[dict],
    max_tokens: int = 256,
    temperature: float = 0.7,
) -> dict:
    """
    Send a chat-completion request to the llama.cpp /v1/chat/completions endpoint.
    Returns the raw JSON response from llama.cpp.
    """
    payload = {
        "model": "phi-3-mini",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
        resp = await client.post(
            f"{LLAMA_CPP_BASE_URL}/v1/chat/completions",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


# ─── Endpoints ───────────────────────────────────────────────────────────────

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def root_ui():
    """Serve the beautiful Chat frontend UI."""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and llama.cpp backend connectivity."""
    llama_status = "unreachable"
    model_loaded = False

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Try the /health endpoint first (llama.cpp native)
            try:
                resp = await client.get(f"{LLAMA_CPP_BASE_URL}/health")
                if resp.status_code == 200:
                    data = resp.json()
                    llama_status = data.get("status", "ok")
                    model_loaded = llama_status == "ok"
                else:
                    llama_status = f"http_{resp.status_code}"
            except Exception:
                # Fallback: try /v1/models
                try:
                    resp = await client.get(f"{LLAMA_CPP_BASE_URL}/v1/models")
                    if resp.status_code == 200:
                        llama_status = "ok"
                        model_loaded = True
                except Exception:
                    pass

    except Exception as exc:
        llama_status = f"error: {exc}"

    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        llama_cpp_url=LLAMA_CPP_BASE_URL,
        llama_cpp_status=llama_status,
        model_loaded=model_loaded,
    )


@app.post("/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate_text(req: GenerateRequest):
    """
    Generate text from a single prompt.
    The prompt is wrapped in a user message and sent to the chat-completion endpoint.
    """
    start = time.perf_counter()

    messages = [{"role": "user", "content": req.prompt}]

    try:
        data = await _call_llama_chat(
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to llama.cpp at {LLAMA_CPP_BASE_URL}. Is the server running?",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"llama.cpp request timed out after {REQUEST_TIMEOUT_S}s",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"llama.cpp returned HTTP {exc.response.status_code}: {exc.response.text[:500]}",
        )

    elapsed_ms = (time.perf_counter() - start) * 1000

    choice = data["choices"][0]
    text = choice["message"]["content"]
    tokens = data.get("usage", {}).get("completion_tokens", len(text.split()))

    if elapsed_ms > RESPONSE_TIME_WARN_MS:
        logger.warning(
            "⚠️  Slow response: %.0f ms (threshold: %d ms) — prompt: %s",
            elapsed_ms,
            RESPONSE_TIME_WARN_MS,
            req.prompt[:80],
        )
    else:
        logger.info("✅ /generate responded in %.0f ms", elapsed_ms)

    return GenerateResponse(
        text=text.strip(),
        tokens_generated=tokens,
        response_time_ms=round(elapsed_ms, 1),
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(req: ChatRequest):
    """
    Multi-turn chat endpoint.
    Accepts a list of messages (system / user / assistant) and returns the next assistant reply.
    """
    start = time.perf_counter()

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        data = await _call_llama_chat(
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to llama.cpp at {LLAMA_CPP_BASE_URL}. Is the server running?",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"llama.cpp request timed out after {REQUEST_TIMEOUT_S}s",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"llama.cpp returned HTTP {exc.response.status_code}: {exc.response.text[:500]}",
        )

    elapsed_ms = (time.perf_counter() - start) * 1000

    choice = data["choices"][0]
    text = choice["message"]["content"]
    tokens = data.get("usage", {}).get("completion_tokens", len(text.split()))

    if elapsed_ms > RESPONSE_TIME_WARN_MS:
        logger.warning(
            "⚠️  Slow response: %.0f ms (threshold: %d ms)",
            elapsed_ms,
            RESPONSE_TIME_WARN_MS,
        )
    else:
        logger.info("✅ /chat responded in %.0f ms", elapsed_ms)

    return ChatResponse(
        message=ChatMessage(role="assistant", content=text.strip()),
        tokens_generated=tokens,
        response_time_ms=round(elapsed_ms, 1),
    )


# ─── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    # Try ports 8000, 8001, 8002
    for port in (8000, 8001, 8002):
        try:
            logger.info("Starting FastAPI server on port %d ...", port)
            uvicorn.run(app, host="0.0.0.0", port=port)
            break
        except OSError as exc:
            if "address already in use" in str(exc).lower() or "10048" in str(exc):
                logger.warning("Port %d in use, trying next...", port)
            else:
                raise
