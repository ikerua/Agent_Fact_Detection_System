Here is a comprehensive development plan to build the architecture outlined in your diagram. The system is divided into two main pipelines: the Audio Extraction phase and the LangGraph Agent Ecosystem.

### Phase 1: Data Ingestion & Transcription (Audio Extraction)

This phase handles the raw input and converts it into actionable text for your agents.

- **Step 1: Input Handling (Video/URL)**
  - Create a module to accept either direct audio/video files or URLs (e.g., YouTube links).
  - _Recommended Tool:_ `yt-dlp` (Python library) to safely and reliably download media from various URLs.
- **Step 2: Download & Audio Extraction**
  - Extract the audio track from the downloaded video files and convert it to a standard format (e.g., MP3 or 16kHz WAV, which Whisper prefers).
  - _Recommended Tool:_ `FFmpeg` (via the `ffmpeg-python` wrapper).
- **Step 3: Whisper Transcriptor**
  - Process the extracted audio to generate a highly accurate text transcript.
  - _Recommended Tool:_ OpenAI's Whisper (either the local open-source library `openai-whisper` for free processing, or the Groq/OpenAI APIs for faster execution).

### Phase 2: Agent Tooling Setup

Before building the orchestrator, you need to define the three core capabilities (nodes) that your LangGraph agent will use, powered by **Gemini Flash** as the base LLM.

- **Node 1: Fact Extractor**
  - **Goal:** Read the raw Whisper transcript and extract verifiable claims or key statements.
  - **Implementation:** Use Gemini Flash with a structured output prompt (e.g., returning a JSON list of standalone claims).
- **Node 2: Bing Search (Búsqueda Bing)**
  - **Goal:** Retrieve external, real-world context for the extracted facts.
  - **Implementation:** Integrate the Bing Web Search API. Create a function that takes a claim from Node 1, formulates a search query, and returns the top snippets.
- **Node 3: Natural Language Inference (NLI)**
  - **Goal:** Determine if the search results support, contradict, or are neutral regarding the extracted facts.
  - **Implementation:** Implement a local NLP model using the `sentence-transformers` library. Specifically, use a Cross-Encoder trained on NLI tasks (e.g., `cross-encoder/nli-deberta-v3-base`). It will take a pair of texts `(Extracted Fact, Bing Search Snippet)` and output an inference score.

### Phase 3: LangGraph Orchestrator Agent

This is the core brain of your ecosystem, routing the data through the tools defined above.

- **Step 1: Define the Graph State**
  - Create a `TypedDict` or Pydantic model to hold the state of the graph. It should include fields for: `raw_transcript`, `extracted_facts`, `search_results`, and `final_nli_analysis`.
- **Step 2: Build the Nodes**
  - Wrap Phase 2's tools into LangGraph node functions:
    - `extract_facts_node(state)`
    - `search_bing_node(state)`
    - `evaluate_nli_node(state)`
- **Step 3: Define Edges and Routing**
  - Set the entry point to the orchestrator (receiving the text from Phase 1).
  - Connect the nodes sequentially as indicated by your dashed lines: `Text` **$\rightarrow$** `Fact Extractor` **$\rightarrow$** `Bing Search` **$\rightarrow$** `NLI Evaluation`.
  - Compile the graph into a runnable LangChain application.

### Phase 4: Integration and Deployment

- **API / Interface:** Wrap the entire pipeline in a FastAPI backend or a Streamlit frontend so users can easily paste a URL and view the final fact-checked results.
- **Error Handling:** Add retry logic for the Bing API and Whisper processing steps, as these can occasionally fail due to network issues or rate limits.

---

Would you like me to start by drafting the Python code for the **Audio Extraction/Whisper pipeline** , or should we jump straight into coding the **LangGraph Orchestrator** ?
