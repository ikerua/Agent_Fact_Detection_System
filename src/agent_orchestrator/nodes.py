import os
import json
import requests
from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from sentence_transformers import CrossEncoder

from .state import GraphState, Fact, NLIAnalysis

# Initialize models
# Assuming GOOGLE_API_KEY is in environment variables
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

# nli-deberta-v3-base outputs contradiction, entailment, neutral
nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-base')

class ExtractedFacts(BaseModel):
    facts: List[str] = Field(description="A list of standalone factual claims extracted from the raw transcript.")

def extract_facts_node(state: GraphState) -> GraphState:
    """
    Node 1: Fact Extractor
    Goal: Read the raw Whisper transcript and extract verifiable claims.
    """
    transcript = state["raw_transcript"]
    
    prompt = PromptTemplate.from_template(
        "You are an expert fact-checker. Extract all verifiable factual claims from the following transcript.\n\n"
        "Transcript: {transcript}\n\n"
        "Return the output as a list of standalone claims."
    )
    
    # Use structured output
    structured_llm = llm.with_structured_output(ExtractedFacts)
    chain = prompt | structured_llm
    
    result = chain.invoke({"transcript": transcript})
    
    facts = []
    for i, claim_str in enumerate(result.facts):
        facts.append(Fact(id=i, claim=claim_str))
        
    return {"extracted_facts": facts}

def search_brave_node(state: GraphState) -> GraphState:
    """
    Node 2: Brave Search
    Goal: Retrieve external context for extracted facts.
    """
    facts = state["extracted_facts"]
    search_results = {}
    
    brave_api_key = os.environ.get("BRAVE_API_KEY")
    brave_search_url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": brave_api_key
    } if brave_api_key else {}
    
    for fact in facts:
        claim_id = fact["id"]
        claim_text = fact["claim"]
        
        if not brave_api_key:
            # Mock search or warning if API key is not provided
            search_results[claim_id] = [f"Mock search result for: {claim_text}. Setup BRAVE_API_KEY."]
            continue
            
        params = {"q": claim_text}
        try:
            response = requests.get(brave_search_url, headers=headers, params=params)
            response.raise_for_status()
            search_data = response.json()
            
            snippets = []
            if "web" in search_data and "results" in search_data["web"]:
                for page in search_data["web"]["results"][:3]: # Take top 3
                    if "description" in page:
                        snippets.append(page["description"])
            search_results[claim_id] = snippets
        except Exception as e:
            print(f"Error searching for '{claim_text}': {e}")
            search_results[claim_id] = []
            
    return {"search_results": search_results}

def evaluate_nli_node(state: GraphState) -> GraphState:
    """
    Node 3: Natural Language Inference (NLI)
    Goal: Determine if search results support, contradict, or are neutral regarding facts.
    """
    facts = state["extracted_facts"]
    search_results = state["search_results"]
    
    analysis = []
    
    # Label mapping for nli-deberta-v3-base: 0: contradiction, 1: entailment, 2: neutral
    label_mapping = {0: "contradiction", 1: "entailment", 2: "neutral"}
    
    for fact in facts:
        claim_id = fact["id"]
        claim_text = fact["claim"]
        snippets = search_results.get(claim_id, [])
        
        for snippet in snippets:
            # Prepare pair: Premise is snippet, Hypothesis is claim
            pair = (snippet, claim_text) 
            scores = nli_model.predict([pair])[0]
            
            # Get the predicted label (argmax)
            predicted_class_id = scores.argmax()
            predicted_label = label_mapping.get(predicted_class_id, "unknown")
            
            analysis.append(NLIAnalysis(
                claim_id=claim_id,
                claim=claim_text,
                snippet=snippet,
                score=float(scores[predicted_class_id]),
                label=predicted_label
            ))
            
    return {"final_nli_analysis": analysis}
