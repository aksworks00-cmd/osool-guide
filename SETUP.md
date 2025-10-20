# Osool Guide - Setup & Deployment Guide

## Overview

This is a **FastAPI application** (not Gradio) configured to run on **Hugging Face Spaces** using Docker SDK.

---

## Prerequisites

1. **Python 3.11+** installed locally
2. **Groq API Key** - Get one from: https://console.groq.com/keys
3. **Hugging Face Account** - For deployment: https://huggingface.co/join

---

## Local Setup

### Step 1: Install Dependencies

```bash
cd /Users/abdulaziz/Desktop/osool_guide
pip install -r requirements.txt
```

**Installed packages:**
- FastAPI + Uvicorn (web server)
- Groq (LLM API client)
- FAISS (vector search)
- sentence-transformers (embeddings)
- And more...

### Step 2: Configure Environment Variables

Create or edit [.env](.env):

```bash
# Get your Groq API key from: https://console.groq.com/keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx  # ← Replace with your actual Groq API key

# Server configuration
HOST=0.0.0.0
PORT=7860
PYTHONUNBUFFERED=1
```

**Important:** The `.env` file is git-ignored for security. Never commit API keys!

### Step 3: Run Locally

```bash
# Option 1: Using uvicorn directly
python -m uvicorn src.server:app --host 0.0.0.0 --port 7860 --reload

# Option 2: Using the server script
python src/server.py --host 0.0.0.0 --port 7860 --reload

# Option 3: Using the main CLI
python src/main.py
```

Open your browser to: **http://localhost:7860**

---

## Deployment to Hugging Face Spaces

### Current Configuration

The [README.md](README.md) already has the correct Hugging Face Space metadata:

```yaml
---
title: Osool Guide
emoji: 🎯
sdk: docker          # ← Uses Docker SDK (not Gradio!)
pinned: false
license: apache-2.0
---
```

### Option 1: Replace Existing Gradio Space (Recommended)

If your current HF Space is running Gradio, this will replace it with FastAPI:

```bash
# Make sure you're on the main branch
git checkout main

# Push to Hugging Face
git push origin main
```

**What happens:**
1. Hugging Face detects `sdk: docker` in README.md
2. Builds container using [Dockerfile](Dockerfile)
3. Runs: `python -m uvicorn src.server:app --host 0.0.0.0 --port 7860`
4. Your FastAPI app goes live!

### Option 2: Create a New Space

If you want to keep the old Gradio version as backup:

1. **Create new Space on Hugging Face:**
   - Go to: https://huggingface.co/new-space
   - Name: `osool_guide_v2` (or any name)
   - SDK: **Docker** (important!)
   - License: Apache 2.0

2. **Update git remote:**
   ```bash
   git remote set-url origin https://aksworks00:YOUR_HF_TOKEN@huggingface.co/spaces/aksworks00/osool_guide_v2
   ```

3. **Push:**
   ```bash
   git push origin main
   ```

### Set Groq API Key on Hugging Face

**Critical:** After pushing, you MUST configure the Groq API key in your Space settings:

1. Go to your Space: `https://huggingface.co/spaces/aksworks00/osool_guide`
2. Click **Settings** tab
3. Scroll to **Repository secrets**
4. Add new secret:
   - **Name:** `GROQ_API_KEY`
   - **Value:** Your Groq API key (starts with `gsk_...`)
5. Click **Save**
6. Space will automatically restart with the new secret

---

## How the Deployment Works

### Build Process

```
1. Hugging Face reads README.md → detects `sdk: docker`
2. Runs Dockerfile:
   - FROM python:3.11-slim
   - COPY requirements.txt → pip install
   - COPY src/, embeddings/, config/, ui/
   - EXPOSE 7860
   - CMD: uvicorn src.server:app --host 0.0.0.0 --port 7860
3. Container starts (~5-10 minutes build time)
4. FastAPI server listens on port 7860
5. Space is live!
```

### Runtime Architecture

```
User Browser
    ↓
https://huggingface.co/spaces/aksworks00/osool_guide
    ↓
FastAPI Server (port 7860)
    ↓
Routes:
    GET  /          → Serve Web UI (ui/index.html)
    GET  /health    → Health check
    GET  /stats     → System statistics
    POST /codify    → Classify asset (main endpoint)
    ↓
NATOCodifierPipeline
    ├─ Stage 1: Query Understanding (Groq LLM)
    ├─ Stage 2: FAISS Vector Search (54,448 items)
    └─ Stage 3: Candidate Selection (Groq LLM)
    ↓
Return: {inc, nsg, nsc, name, definition, confidence, reasoning}
```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'groq'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Error: "GROQ_API_KEY not found"

**Solution:**
- **Local:** Create [.env](.env) with your Groq API key
- **HF Space:** Add `GROQ_API_KEY` in Space Settings → Repository secrets

### Error: "Pipeline not initialized"

**Solution:** Check the Space logs (Logs tab) for errors during startup. The FAISS index must load successfully (~500MB).

### Slow Build on Hugging Face

**Normal:** First build takes 5-10 minutes due to:
- Installing PyTorch (~2GB)
- Installing all dependencies
- Loading embeddings/inc_index.faiss (~500MB)

Subsequent builds are faster (cached layers).

---

## File Structure

```
osool_guide/
├── README.md              # HF Space metadata (sdk: docker)
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
├── .env                   # Local environment (git-ignored)
├── .gitignore             # Protect secrets
│
├── src/
│   ├── server.py          # FastAPI app
│   ├── main.py            # CLI interface
│   ├── pipeline/
│   │   ├── codifier_pipeline.py
│   │   ├── stage1_understanding.py
│   │   ├── stage2_retrieval.py
│   │   └── stage3_selection.py
│   └── utils/
│       ├── groq_client.py
│       ├── config_loader.py
│       └── logger.py
│
├── ui/
│   ├── index.html         # Web interface
│   └── static/
│       ├── css/style.css
│       └── js/app.js
│
├── embeddings/
│   ├── inc_index.faiss    # Vector index (~500MB)
│   └── metadata.pkl       # Item metadata (~100MB)
│
└── config/
    └── config.yaml        # System configuration
```

---

## API Usage Examples

### Web UI
```
1. Open: https://huggingface.co/spaces/aksworks00/osool_guide
2. Enter: "Boeing 737 gas turbine"
3. Click "Classify Asset"
4. View results with NATO codes
```

### cURL
```bash
curl -X POST https://aksworks00-osool-guide.hf.space/codify \
  -H "Content-Type: application/json" \
  -d '{"query": "M4 rifle"}'
```

### Python
```python
import requests

response = requests.post(
    "https://aksworks00-osool-guide.hf.space/codify",
    json={"query": "desktop computer"}
)

result = response.json()
print(f"INC: {result['inc']}")
print(f"Name: {result['name']}")
print(f"Confidence: {result['confidence']}")
```

---

## Next Steps

1. **Get Groq API Key:** https://console.groq.com/keys
2. **Add to .env locally** (for testing)
3. **Test locally:** `python -m uvicorn src.server:app --port 7860 --reload`
4. **Push to HF:** `git push origin main`
5. **Configure HF secret:** Add `GROQ_API_KEY` in Space Settings
6. **Monitor build:** Watch Logs tab on HF Space
7. **Test live:** Open your Space URL

---

## Resources

- **Groq Console:** https://console.groq.com
- **Hugging Face Spaces Docs:** https://huggingface.co/docs/hub/spaces
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **FAISS Docs:** https://github.com/facebookresearch/faiss

---

**Built with Claude Code** • https://claude.com/claude-code
