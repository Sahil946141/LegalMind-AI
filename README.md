# AI-Powered Legal Document Analyzer

A comprehensive full-stack application that leverages AI to analyze legal documents, contracts, and case files. Built with FastAPI, React, and an advanced Agentic RAG system with intelligent query understanding, multi-LLM fallback capabilities, and a local ML engine for clause and risk classification.

---

## ⭐ Key Highlights

- 🤖 **Agentic RAG Pipeline**: Intelligent question-answering with automatic query rewriting, multi-LLM fallback (Gemini + Groq), confidence scoring, and citation tracking
- 🧠 **Local ML Engine**: Offline clause classification and risk scoring using trained Logistic Regression models — no external API required
- 📊 **RAG Evaluation Framework**: Built-in pipeline to evaluate RAG performance with keyword matching, latency tracking, and accuracy metrics
- ⚡ **Celery + Redis**: Asynchronous document processing with distributed task queue for scalable document ingestion
- 🔐 **Secure & Fast**: JWT authentication, PostgreSQL persistence, Pinecone vector storage

---

## 🧠 ML Engine (Local Clause & Risk Classification)

The ML Engine is a fully offline, self-contained module that classifies legal document clauses by type and risk level — no external LLM or API call required.

### How It Was Built

The models were trained in `app/ml engine/machine_learning.ipynb` using a labeled legal contract dataset (`legal_contract_clauses.csv`):

1. **Embeddings**: Each clause was encoded using `SentenceTransformer` (`all-MiniLM-L6-v2`) into a 384-dimensional vector.
2. **Clause Classifier**: A `LogisticRegression` model trained to predict the **clause type** (e.g., payment, termination, confidentiality, liability).
3. **Risk Classifier**: A separate `LogisticRegression` model trained to predict the **risk level** (e.g., high, medium, low) of each clause.
4. All four artifacts (`clause_classifier.pkl`, `clause_label_encoder.pkl`, `risk_classifier.pkl`, `risk_label_encoder.pkl`) are serialized with `joblib` and stored in `app/ml engine/`.

### Architecture

```
Document Chunks
      │
      ▼
SentenceTransformer (all-MiniLM-L6-v2)
      │ 384-dim embeddings
      ├──────────────────────────────────────┐
      ▼                                      ▼
Clause Classifier (LogisticRegression)   Risk Classifier (LogisticRegression)
      │                                      │
      ▼                                      ▼
Clause Type Label                        Risk Level Label
(e.g., "Termination")                    (e.g., "High")
      │                                      │
      └─────────────────┬────────────────────┘
                        ▼
              Entity Extraction (Regex)
         Dates | Money | Companies | Notice Periods
                        │
                        ▼
              Structured Analysis Result
         { classification, risks, entities }
```

### Key Files

| File | Description |
|---|---|
| `app/ml engine/machine_learning.ipynb` | Jupyter notebook for training both models |
| `app/ml engine/clause_classifier.pkl` | Trained clause type classifier |
| `app/ml engine/clause_label_encoder.pkl` | Label encoder for clause types |
| `app/ml engine/risk_classifier.pkl` | Trained risk level classifier |
| `app/ml engine/risk_label_encoder.pkl` | Label encoder for risk levels |
| `app/rag/ml_clause_analyzer.py` | Runtime analyzer: loads models, runs inference |
| `app/test_ml_integration.py` | Integration test for the ML pipeline |

### MLClauseAnalyzer — Core Class

`MLClauseAnalyzer` in `app/rag/ml_clause_analyzer.py` manages model loading and inference:

```python
from app.rag.ml_clause_analyzer import get_analyzer

analyzer = get_analyzer()
result = analyzer.analyze_chunk("Either party may terminate with 30 days notice.")
# → { "classification": "Termination", "risks": "Medium", "entities": "Notice: 30 days notice" }
```

**Batch processing** (used during document ingestion):

```python
from app.rag.ml_clause_analyzer import analyze_document_chunks

results = analyze_document_chunks(chunks)
# Each result: { classification, risks, entities, source_text, filename, page, chunk_index }
```

### Entity Extraction

In addition to ML predictions, the analyzer runs regex-based extraction to identify:

- **Money**: `$50,000`, `USD 10,000`, `dollars`
- **Dates**: ISO dates, named months
- **Companies**: Entities ending in Inc., LLC, Corp., Ltd., etc.
- **Notice Periods**: `30 days notice`, `2 weeks prior notice`

### Integration with Document Pipeline

When a document is processed through the Celery worker, `analyze_document_chunks()` replaces the prior Ollama-based analysis:

```
Document ingested
      │
      ▼
Chunks generated → Embeddings → Pinecone upsert
                                      │
                                      ▼
                          ML Clause Analysis (offline)
                          clause type + risk + entities
                                      │
                                      ▼
                          Stored in PostgreSQL (doc_analysis)
```

### Running the Integration Test

```bash
python app/test_ml_integration.py
```

Expected output:

```
✅ ML Models Loading & Basic Analysis PASSED
✅ Document Chunks Analysis PASSED
🎉 All ML integration tests passed!
```

### Retraining the Models

To retrain with new data:

1. Open `app/ml engine/machine_learning.ipynb` in Jupyter or Google Colab.
2. Replace `legal_contract_clauses.csv` with your updated dataset (columns: `clause_text`, `clause_type`, `risk_level`).
3. Run all cells — models are saved automatically as `.pkl` files.
4. Replace the existing `.pkl` files in `app/ml engine/`.

---

## 🚀 Agentic RAG Pipeline (Core Feature)

The Agentic RAG system is the heart of this application, designed for robust and intelligent document Q&A. Unlike basic RAG systems, it employs a multi-stage agentic approach:

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGENTIC RAG PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐   │
│  │   Question   │───▶│  Initial Query    │───▶│  Strong Evidence?      │   │
│  │   (Input)    │    │  Retrieval       │    │  (Score ≥ 0.45)        │   │
│  └──────────────┘    │  (Top-K=10)      │    └───────────┬─────────────┘   │
│                      └──────────────────┘                │                 │
│                                                        ▼                   │
│                      ┌──────────────────┐    ┌─────────────────────────┐   │
│                      │  Query Rewrite   │◀───│  No? Try Rewrite       │   │
│                      │  (Gemini → Groq) │    │  (Budget: 2.5s)        │   │
│                      └────────┬─────────┘    └─────────────────────────┘   │
│                               │                                             │
│                               ▼                                             │
│                      ┌──────────────────┐                                  │
│                      │  Retry Query     │                                  │
│                      │  Retrieval       │                                  │
│                      │  (Rewritten Q)   │                                  │
│                      └────────┬─────────┘                                  │
│                               │                                             │
│                               ▼                                             │
│              ┌────────────────────────────────────┐                        │
│              │      Confidence Scoring            │                        │
│              │  ┌─────────────────────────────┐   │                        │
│              │  │ HIGH:   Score ≥ 0.45, ≥2 cite│   │                        │
│              │  │ MEDIUM: Score ≥ 0.30, ≥1 cite│   │                        │
│              │  │ LOW:    Has citations        │   │                        │
│              │  │ NONE:   No evidence found    │   │                        │
│              │  └─────────────────────────────┘   │                        │
│              └───────────────────┬────────────────┘                        │
│                                  │                                          │
│                                  ▼                                          │
│              ┌────────────────────────────────────────────┐                │
│              │           LLM Answer Generation            │                │
│              │  ┌──────────────────────────────────────┐  │                │
│              │  │  Primary: Gemini (gemini-2.5-flash)  │  │                │
│              │  │  Fallback: Groq (qwen/qwen3-32b)     │  │                │
│              │  │  Local:    Extractive Fallback       │  │                │
│              │  └──────────────────────────────────────┘  │                │
│              └───────────────────┬────────────────────────┘                │
│                                  │                                          │
│                                  ▼                                          │
│                      ┌──────────────────┐                                  │
│                      │  Final Response  │                                  │
│                      │  + Citations     │                                  │
│                      │  + Confidence    │                                  │
│                      │  + Latency       │                                  │
│                      └──────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---|---|
| Intelligent Query Rewriting | Automatically rewrites user questions into optimized legal search queries using Gemini (primary) or Groq (fallback) |
| Multi-LLM Fallback | Graceful degradation: Gemini → Groq → Local Extractive Fallback ensures the system always returns an answer |
| Confidence Scoring | Automatic confidence levels (high/medium/low/none) based on retrieval scores and citation count |
| Complex Question Detection | Identifies questions about risks, liability, obligations, termination, etc. and provides enriched responses |
| Evidence Thresholds | Smart retrieval with BEST_SCORE_STRONG=0.45 and BEST_SCORE_MIN=0.30 for quality control |
| Citation Tracking | Every answer includes source citations with filename, page number, chunk index, and relevance score |
| Latency Tracking | Full request latency logged for performance monitoring |

### Agentic vs Basic RAG

```python
# Basic RAG (app/rag/basic_rag.py)
question → embed → retrieve → LLM → answer

# Agentic RAG (app/rag/agentic_rag.py)
question → embed → retrieve → check evidence →
  if weak evidence:
    rewrite query → re-retrieve
  confidence scoring →
  LLM (with fallback) →
  answer + citations + confidence + latency
```

### Configuration (Environment Variables)

```bash
# Embedding Model
ST_MODEL_NAME=all-MiniLM-L6-v2

# Gemini (Primary LLM)
GEMINI_API_KEY=your_key
GEMINI_REWRITE_MODEL=gemini-2.5-flash
GEMINI_ANSWER_MODEL=gemini-2.5-flash

# Groq (Fallback LLM)
GROQ_API_KEY=your_key
GROQ_REWRITE_MODEL=gemma2-9b-it
GROQ_ANSWER_MODEL=qwen/qwen3-32b

# Retrieval Thresholds
BEST_SCORE_STRONG=0.45
BEST_SCORE_MIN=0.30

# Pinecone Vector DB
PINECONE_API_KEY=your_key
PINECONE_INDEX=legal-doc-analyzer
```

---

## 📊 RAG Evaluation Pipeline

The project includes a comprehensive evaluation framework to measure RAG performance:

### Evaluation Script (`app/rag/evaluate_pipeline.py`)

```bash
# Setup evaluation data
python app/rag/eval.py

# Run evaluation
python app/rag/evaluate_pipeline.py
```

### Metrics Tracked

| Metric | Description |
|---|---|
| Accuracy | Percentage of questions answered correctly |
| Match Type | exact_match, keyword_match, partial_keyword_match, no_match |
| Latency (ms) | Time taken for each Q&A request |
| Confidence Distribution | High/Medium/Low/None confidence counts |
| Rewrite Statistics | How often query rewrite was used |
| Category Breakdown | Performance by question category |

### Sample Output

```json
{
  "summary": {
    "total_questions": 20,
    "passed": 18,
    "failed": 2,
    "accuracy": 0.90,
    "by_category": {
      "party_info": {"total": 5, "passed": 5, "failed": 0},
      "termination": {"total": 4, "passed": 3, "failed": 1}
    },
    "rewrite_stats": {"used": 8, "not_used": 12}
  }
}
```

---

## ⚡ Celery Worker + Redis Architecture

Document processing is handled asynchronously via Celery with Redis as the message broker:

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐
│   FastAPI   │────▶│    Redis    │────▶│     Celery Worker          │
│   Server    │     │   (Broker)  │     │  (Document Processing)     │
└─────────────┘     └─────────────┘     │                             │
      │                                   │  1. Load Document           │
      │                                   │  2. Chunk Documents         │
      │                                   │  3. Generate Embeddings     │
      │                                   │  4. Upsert to Pinecone      │
      │                                   │  5. ML Clause Analysis      │
      │                                   │  6. Update Status           │
      │                                   └─────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│           PostgreSQL                     │
│  (Users, Documents, QnA Logs)           │
└─────────────────────────────────────────┘
```

### Starting the Worker

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker (Windows)
celery -A app.worker.celery_app worker --loglevel=info --pool=solo

# Terminal 3: Start Celery Worker (Linux/Mac)
celery -A app.worker.celery_app worker --loglevel=info

# Terminal 4: Start FastAPI
python run_server.py
```

---

## 🏗️ Full Architecture

### Backend (FastAPI)

- **API Server**: FastAPI with async support
- **Database**: PostgreSQL with connection pooling
- **Authentication**: JWT tokens with secure password hashing
- **Task Queue**: Celery with Redis for async processing
- **AI/ML**:
  - Google Gemini (primary LLM)
  - Groq (fallback LLM)
  - Sentence Transformers (embeddings)
  - Pinecone (vector database)
  - Local ML Engine (offline clause & risk classification)

### Frontend (React + TypeScript)

- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom components
- **State Management**: React Context + Custom hooks
- **Routing**: React Router v6
- **UI Components**: Radix UI primitives with custom styling
- **Build Tool**: Vite for fast development and building

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-legal-document-analyzer.git
cd ai-legal-document-analyzer
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "
from app.main import app
import requests
requests.post('http://localhost:8000/init-db')
"
```

### 3. Frontend Setup

```bash
# Install dependencies
npm install

# Setup environment (optional)
cp .env.example .env.local
# Edit .env.local if needed
```

### 4. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A app.worker.celery_app worker --loglevel=info --pool=solo

# Terminal 3: Start Backend
python run_server.py

# Terminal 4: Start Frontend
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 📋 Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|---|---|---|
| `DB_*` | Database connection settings | ✅ |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | ✅ |
| `REDIS_URL` | Redis connection URL | ✅ |
| `PINECONE_API_KEY` | Pinecone vector database API key | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `GROQ_API_KEY` | Groq API key (fallback LLM) | ✅ |
| `ST_MODEL_NAME` | SentenceTransformer model name | ⬜ (default: all-MiniLM-L6-v2) |

---

## 📁 Project Structure

```
├── app/                        # Backend application
│   ├── auth/                   # Authentication modules
│   ├── core/                   # Core settings and security
│   ├── db/                     # Database connections and queries
│   ├── ml engine/              # ⭐ Local ML models
│   │   ├── machine_learning.ipynb      # Model training notebook
│   │   ├── clause_classifier.pkl       # Trained clause type classifier
│   │   ├── clause_label_encoder.pkl    # Clause type label encoder
│   │   ├── risk_classifier.pkl         # Trained risk level classifier
│   │   └── risk_label_encoder.pkl      # Risk level label encoder
│   ├── rag/                    # RAG pipeline and AI processing
│   │   ├── agentic_rag.py      # ⭐ Agentic RAG implementation
│   │   ├── basic_rag.py        # Basic RAG implementation
│   │   ├── ml_clause_analyzer.py  # ⭐ ML-based clause & risk analysis
│   │   ├── pipeline.py         # Document processing pipeline
│   │   ├── ingest.py           # Document ingestion
│   │   ├── eval.py             # Evaluation data setup
│   │   ├── evaluate_pipeline.py # RAG evaluation framework
│   │   └── clause_analyzis.py  # Clause analysis
│   ├── schemas/                # Pydantic models
│   ├── users/                  # User management
│   ├── worker/                 # Celery tasks
│   │   ├── celery_app.py       # Celery configuration
│   │   └── tasks.py            # Background tasks
│   ├── test_ml_integration.py  # ⭐ ML integration tests
│   └── main.py                 # FastAPI application
├── src/                        # Frontend application
│   ├── components/             # React components
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utility libraries
│   ├── pages/                  # Page components
│   └── test/                   # Frontend tests
├── sql/                        # Database schema files
├── public/                     # Static assets
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
└── README.md                   # This file
```

---

## 🛠️ Development

### Backend Development

```bash
# Run with auto-reload
python run_server.py

# Run tests
python -m pytest

# Run ML integration tests
python app/test_ml_integration.py

# Check code style
black app/
flake8 app/

# Run RAG evaluation
python app/rag/evaluate_pipeline.py
```

### Frontend Development

```bash
# Start development server
npm run dev

# Run tests
npm run test

# Build for production
npm run build

# Lint code
npm run lint
```

---

## 🔧 Configuration

### Database Setup

```sql
CREATE DATABASE legal_analyzer;
CREATE USER legal_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE legal_analyzer TO legal_user;
```

Run database initialization:

```bash
curl -X POST http://localhost:8000/init-db
```

### Redis Setup

```bash
# Windows: Download Redis from https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt install redis-server
# Mac: brew install redis

# Start Redis
redis-server

# Check connection
redis-cli ping
```

---

## 🚀 Deployment

### Using Docker (Recommended)

```bash
docker-compose up --build
```

### Manual Deployment

- **Backend**: Deploy to any Python-compatible platform (AWS, GCP, Heroku)
- **Frontend**: Build and deploy to CDN (Vercel, Netlify, AWS S3)
- **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- **Redis**: Use managed Redis (AWS ElastiCache, Redis Cloud)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [React](https://react.dev/) for the frontend framework
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI capabilities
- [Groq](https://groq.com/) for fast LLM inference
- [Pinecone](https://www.pinecone.io/) for vector database
- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [scikit-learn](https://scikit-learn.org/) for ML classification models
- [Celery](https://docs.celeryq.dev/) for distributed task queue
- [Redis](https://redis.io/) for message broker
- [Radix UI](https://www.radix-ui.com/) for accessible UI components

---

## 📞 Support

If you have any questions or need help, please:

- Check the [Issues](../../issues) page
- Create a new issue if your problem isn't already reported
- Provide detailed information about your environment and the issue
