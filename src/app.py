import os
import sys
import shutil
from typing import Optional

# Add the project root to sys.path so 'src' can be imported easily from anywhere
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables (like API keys)
load_dotenv()

from src.data_ingestion_transcription.audio_extractor import AudioExtractor
from src.agent_orchestrator.graph import build_graph
from src.agent_orchestrator.state import GraphState

app = FastAPI(title="Fact Detection System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str

class TextRequest(BaseModel):
    transcript: str

# Initialize AudioExtractor at startup to load Whisper
# You can change model size. 'base' takes ~1GB VRAM/RAM
audio_extractor = AudioExtractor("large-v3")

# Build the LangGraph application
graph_app = build_graph()

@app.post("/transcribe_only")
async def transcribe_only_endpoint(
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Endpoint to transcribe either a video URL or an uploaded audio/video file.
    """
    try:
        if file:
            print(f"Transcribing uploaded file: {file.filename}")
            os.makedirs("downloads", exist_ok=True)
            file_path = os.path.join("downloads", file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            transcript = audio_extractor.transcribe(file_path)
            
            return {"transcript": transcript}
            
        elif url:
            print(f"Transcribing URL: {url}")
            transcript = audio_extractor.process_url(url)
            
            return {"transcript": transcript}
            
        else:
            raise HTTPException(status_code=400, detail="Debes proporcionar una URL o subir un archivo de audio/video.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_url")
async def process_url_endpoint(
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Endpoint to process a video URL or audio File through the entire pipeline.
    """
    try:
        if file:
            print(f"Processing uploaded file: {file.filename}")
            os.makedirs("downloads", exist_ok=True)
            file_path = os.path.join("downloads", file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            transcript = audio_extractor.transcribe(file_path)
            
        elif url:
            print(f"Processing URL: {url}")
            transcript = audio_extractor.process_url(url)
            
        else:
            raise HTTPException(status_code=400, detail="Debes proporcionar una URL o subir un archivo.")

        # Phase 2 & 3: Fact Checking Pipeline
        print("Starting Agent Ecosystem...")
        initial_state = {
            "raw_transcript": transcript,
            "extracted_facts": [],
            "search_results": {},
            "final_nli_analysis": []
        }
        
        result_state = graph_app.invoke(initial_state)
        
        return {
            "transcript": transcript,
            "results": result_state["final_nli_analysis"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_text")
async def analyze_text_endpoint(request: TextRequest):
    """
    Endpoint to directly analyze a raw transcript without downloading audio.
    """
    try:
        # Phase 2 & 3: Fact Checking Pipeline
        print("Starting Agent Ecosystem directly from text...")
        initial_state = {
            "raw_transcript": request.transcript,
            "extracted_facts": [],
            "search_results": {},
            "final_nli_analysis": []
        }
        
        result_state = graph_app.invoke(initial_state)
        
        return {
            "transcript": request.transcript,
            "results": result_state["final_nli_analysis"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)

app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(static_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
