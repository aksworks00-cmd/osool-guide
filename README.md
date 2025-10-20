---
title: Osool Guide
emoji: 🎯
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: apache-2.0
short_description: NATO Asset Codifier with AI-powered classification
---

# 🎯 Osool Guide - NATO Asset Codifier

Automatically classify military assets according to NATO Item Name Codes (INC).

## Features

- 🚀 **Fast Classification**: Powered by Groq API (llama-3.3-70b)
- 🔍 **Semantic Search**: 54,448 NATO items indexed with FAISS
- 🇸🇦 **Bilingual**: Full English and Arabic support
- ⚡ **Real-time**: ~1.5 second response time

## How to Use

1. Enter an asset description (e.g., "helmet", "computer", "rifle")
2. Click "Classify Asset"
3. View NATO codes (INC, NSG, NSC) and detailed definitions

## Technology

- **Backend**: FastAPI + Python
- **AI**: Groq API (llama-3.3-70b-versatile)
- **Search**: FAISS vector similarity
- **Embeddings**: sentence-transformers (nomic-embed-text-v1.5)

---

Built with Claude Code • https://claude.com/claude-code
