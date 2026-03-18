# Agent Fact Detection System

This project implements an agentic system that extracts audio from media URLs, transcribes it, and evaluates the factual claims made in the transcript using a LangGraph-based workflow.

## Architecture Pipeline

### Phase 1: Data Ingestion & Transcription
- Downloads audio from video paths via `yt-dlp`.
- Converts the audio efficiently using `ffmpeg`.
- Transcribes the audio locally using `openai-whisper`.

### Phase 2 & 3: Fact Checking Agent Ecosystem
Powered by **Gemini Flash**, **Brave Web Search**, and **Sentence Transformers**:
- **Fact Extractor Node:** Extracts verifiable claims from transcript.
- **Brave Search Node:** Retrieves top results to support/evaluate claims.
- **NLI Evaluation Node:** Uses Cross-Encoder model (`cross-encoder/nli-deberta-v3-base`) to score the relationship (entailment, neutral, contradiction).

## Setup & Installation

**Usando `uv` (Recomendado por su rendimiento):**

1. Create a python virtual environment:
   ```bash
   uv venv
   # On Windows: .venv\Scripts\activate
   # On Mac/Linux: source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
   **Note:** You must have `ffmpeg` installed on your system path for whisper to process audio. (Windows: Download ffmpeg and add to PATH, or use `winget install ffmpeg`).

3. Setup API Keys:
   Copy `.env.example` to `.env` and fill out your keys:
   ```env
   GOOGLE_API_KEY="your_gemini_api_key_here"
   BRAVE_API_KEY="your_brave_search_api_key_here"
   ```

## Running the API Server

Start the FastAPI application:
```bash
python src/app.py
```

### Endpoints

- **POST /process_url**
  Body `{"url": "<youtube_or_video_url>"}`
  Downloads the audio, transcribes it, and runs the fact-checking ecosystem.

- **POST /analyze_text**
  Body `{"transcript": "<raw_text>"}`
  Directly runs the fact-checking agent on provided text.

- **POST /transcribe_only**  
  *(Form-Data Request)*  
  Puedes enviar **una de las siguientes opciones**:
  - Parámetro de texto `url`: `<youtube_or_video_url>`
  - Archivo adjunto `file`: Sube directamente un MP3, WAV, MP4, etc.  
  Descarga el audio de la URL o directamente lee el archivo pasándole el contenido al transcriptor local, omitiendo los agentes NLI.

The API runs by default on http://localhost:8000. You can visit http://localhost:8000/docs for the Swagger UI interface.
