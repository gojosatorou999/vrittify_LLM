# Vrittify LLM

A private, locally-hosted LLM wrapper using **Phi-3 Mini** on **llama.cpp**, wrapped securely with a **FastAPI** backend, and presented through a beautifully responsive Custom HTML/CSS Frontend Chat UI.

No cloud, no API keys, total privacy!

## Features
- **Local AI:** Runs completely offline using the lightweight but powerful Microsoft Phi-3 Mini model.
- **FastAPI Backend Structure:** Native `/chat` and `/generate` endpoints tracking token speed and server latency.
- **Dynamic Frontend GUI:** Beautiful glassmorphism UI integrated straight into the index route (`GET /`).
- **Team Ready:** Fully compatible with Ngrok tunneling allowing seamless sharing of your secure local engine to remote teammates.

---

## Getting Started

### 1. Requirements & Setup
Since `llama.cpp` executes natively, having Microsoft Visual C++ compiled libraries is natively required. 

Install the required python packages:
```bash
pip install -r requirements.txt
```

*(Note: Ensure you download the `Phi-3-mini-4k-instruct-q4.gguf` model and place it inside the `/models` directory, and your `llama-server.exe` inside the `/llama-cpp` directory!)*

### 2. How to Run

Open two separate terminals and run these startup scripts:

**Terminal 1 (Backend Engine):**
```powershell
.\start_llama.ps1
```
*This spins up the llama.cpp server and allocates your local memory to host the LLM.*

**Terminal 2 (API Gateway & Web App):**
```powershell
.\start_api.ps1
```
*This starts the FastAPI wrapper bridging your backend and frontend. Connects to `localhost:8000` by default.*

### 3. Usage
Simply open your browser and navigate to:
[http://localhost:8000](http://localhost:8000)

If you prefer testing endpoints manually with Swagger Documentation:
[http://localhost:8000/docs](http://localhost:8000/docs)

---

## How to Share Remotely
If you want to spin up an instant public URL to share with your friends or team without port-forwarding:

1. Setup an account at [Ngrok](https://ngrok.com)
2. Load your Ngrok authtoken into your terminal: `ngrok config add-authtoken <YOUR_TOKEN>`
3. Run the HTTP tunnel routing to your FastAPI port: `ngrok http 8000`

Send the generated `https://[link].ngrok-free.dev` link. Anyone accessing it will land on your custom GUI!
