import os
import sys

# Add the project root to sys.path so 'src' can be imported easily from anywhere
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables (like API keys)
load_dotenv()

from src.data_ingestion_transcription.audio_extractor import AudioExtractor
from src.agent_orchestrator.graph import build_graph
from src.agent_orchestrator.state import GraphState

app = FastAPI(title="Fact Detection System API")

class URLRequest(BaseModel):
    url: str

class TextRequest(BaseModel):
    transcript: str

# Initialize AudioExtractor at startup to load Whisper
# You can change model size. 'base' takes ~1GB VRAM/RAM
audio_extractor = AudioExtractor("base")

# Build the LangGraph application
graph_app = build_graph()

@app.post("/process_url")
async def process_url_endpoint(request: URLRequest):
    """
    Endpoint to process a video URL through the entire pipeline.
    """
    try:
        # Phase 1: Download & Transcribe
        print(f"Processing URL: {request.url}")
        transcript = audio_extractor.process_url(request.url)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
