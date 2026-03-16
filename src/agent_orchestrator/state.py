from typing import TypedDict, List, Dict, Any

class Fact(TypedDict):
    id: int
    claim: str

class NLIAnalysis(TypedDict):
    claim_id: int
    claim: str
    snippet: str
    score: float
    label: str

class GraphState(TypedDict):
    raw_transcript: str
    extracted_facts: List[Fact]
    search_results: Dict[int, List[str]]
    final_nli_analysis: List[NLIAnalysis]
