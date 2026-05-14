# ✈️ Travel Agency AI Chatbot (RAG)

An intelligent travel assistant chatbot built with **Retrieval-Augmented Generation (RAG)**. It answers user queries using your internal travel documents (PDFs, FAQs, service guides) and provides accurate, context-aware responses, including booking links and related travel services.

---

## 🚀 Features

- ✅ Answer travel-related questions: bookings, cancellations, itinerary changes, destinations, services.
- ✅ RAG-powered: responses are grounded in your own documents.
- ✅ Structured JSON responses: answer + booking link + related services.
- ✅ Source citations: show the documents used for transparency.
- ✅ Escalation logic: automatically route complex or ambiguous queries to human support.
- ✅ Easy to extend with new documents and APIs.
- ✅ Multi-turn conversation support via Streamlit chat interface.

---

## 🏗 Architecture

The system follows a modular architecture:

1. **User Interface (Streamlit)**
   - Chat interface for customer queries.

2. **API Layer (FastAPI)**
   - Handles requests from UI.
   - Orchestrates the RAG pipeline.
   - Returns structured JSON responses.

3. **Retrieval & Generation (LangChain + LLM)**
   - Vector search with FAISS.
   - Context retrieval and prompt construction.
   - Generates answers using LLM (OpenAI, LLaMA, etc.)

4. **Knowledge Base**
   - PDF documents, FAQs, service guides.
   - Stored as vector embeddings in FAISS.

---

## 📁 Project Structure

travel-chatbot-rag/
├── app/
│ ├── main.py # FastAPI entry point
│ ├── api/ # API routes
│ ├── rag/ # RAG pipeline (retrieval + LLM)
│ └── ingest.py # Script to create FAISS vectorstore
├── data/ # PDF documents for ingestion
├── vectorstore/ # FAISS index (auto-generated)
├── ui/
│ └── streamlit_app.py # Chat UI
├── requirements.txt # Python dependencies
└── .env # Environment variables (API keys)


---

## 🛠 Tech Stack

- **Python 3.11+** – backend and scripting  
- **FastAPI** – API layer  
- **Streamlit** – frontend chat interface  
- **LangChain** – RAG orchestration  
- **FAISS** – vector search / retrieval  
- **OpenAI API** – LLM for response generation  
- **PyPDF** – PDF document parsing  
- **Pydantic** – structured validation  

---

## ⚡ Quick Start

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/travel-chatbot-rag.git
cd travel-chatbot-rag

### 2️⃣ Setup environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

Create a .env file in the root directory:
OPENAI_API_KEY=your_openai_api_key_here

### 3️⃣ Ingest documents (build vectorstore)

```bash
python app/ingest.py

### 4️⃣ Start FastAPI server

```bash
uvicorn app.main:app --reload

### 5️⃣ Start Streamlit UI

```bash
streamlit run ui/streamlit_app.py

Open your browser at http://localhost:8501
and start chatting.
