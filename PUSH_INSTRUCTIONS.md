# Push to Hugging Face - Instructions

All files are ready and committed! Now you need to push to Hugging Face.

## Step 1: Get Your HF Access Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name: "osool_guide_deploy"
4. Type: Select **"Write"** access
5. Click "Generate token"
6. **Copy the token** (it looks like: `hf_xxxxxxxxxxxxxxxxxxxxx`)

## Step 2: Push to HuggingFace

Run these commands in your terminal:

```bash
cd /Users/aksalmutlaq/osool_guide

# Configure git to use your HF username
git config user.name "aksworks00"
git config user.email "your-email@example.com"

# Push to HF (it will ask for username and password)
git push origin main
```

When prompted:
- **Username**: `aksworks00`
- **Password**: Paste your HF access token (hf_xxxxxxxxxxxxxxxxxxxxx)

## Alternative: Use Token in URL

If the above doesn't work, try:

```bash
cd /Users/aksalmutlaq/osool_guide

git remote set-url origin https://aksworks00:YOUR_HF_TOKEN@huggingface.co/spaces/aksworks00/osool_guide

git push origin main
```

Replace `YOUR_HF_TOKEN` with your actual token.

## What Happens Next

After pushing:

1. HF will start building your Space (~5-10 minutes)
2. Go to: https://huggingface.co/spaces/aksworks00/osool_guide
3. Click the "Logs" tab to watch the build progress
4. Once built, your app will be live!

## Files Pushed (Ready!)

✅ app.py - Gradio interface
✅ requirements.txt - Dependencies
✅ src/ - All source code
✅ embeddings/ - FAISS index (170MB)
✅ config/ - Configuration

**Note**: Your GROQ_API_KEY secret is already configured in HF Space settings!

---

Everything is ready on your local side. Just need to push!
