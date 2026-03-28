# 🏛️ AI-Powered Legal Document Analyzer

A comprehensive full-stack application that leverages AI to analyze legal documents, contracts, and case files. Built with FastAPI, React, and advanced RAG (Retrieval-Augmented Generation) capabilities.

## ✨ Features

- **📄 Document Upload & Processing**: Support for PDF, DOCX, TXT, and RTF files
- **🤖 AI-Powered Analysis**: Advanced document analysis using Google Gemini and vector embeddings
- **💬 Interactive Q&A**: Ask questions about your documents with contextual answers
- **🔍 Smart Search**: Vector-based semantic search through document content
- **📊 Risk Assessment**: Automated identification of legal risks and key clauses
- **📑 Page-wise Analysis**: Detailed breakdown of document content by page
- **🔐 Secure Authentication**: JWT-based user authentication and authorization
- **⚡ Real-time Processing**: Asynchronous document processing with Celery

## 🏗️ Architecture

### Backend (FastAPI)
- **API Server**: FastAPI with async support
- **Database**: PostgreSQL with connection pooling
- **Authentication**: JWT tokens with secure password hashing
- **Task Queue**: Celery with Redis for async processing
- **AI/ML**: Google Gemini LLM + Sentence Transformers + Pinecone vector DB

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom components
- **State Management**: React Context + Custom hooks
- **Routing**: React Router v6
- **UI Components**: Radix UI primitives with custom styling
- **Build Tool**: Vite for fast development and building

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

## 📋 Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_*` | Database connection settings | ✅ |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | ✅ |
| `REDIS_URL` | Redis connection URL | ✅ |
| `PINECONE_API_KEY` | Pinecone vector database API key | ✅ |
| `GOOGLE_API_KEY` | Google Gemini API key | ✅ |

## 🛠️ Development

### Backend Development

```bash
# Run with auto-reload
python run_server.py

# Run tests
python -m pytest

# Check code style
black app/
flake8 app/
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

## 📁 Project Structure

```
├── app/                    # Backend application
│   ├── auth/              # Authentication modules
│   ├── core/              # Core settings and security
│   ├── db/                # Database connections and queries
│   ├── rag/               # RAG pipeline and AI processing
│   ├── schemas/           # Pydantic models
│   ├── users/             # User management
│   ├── worker/            # Celery tasks
│   └── main.py            # FastAPI application
├── src/                   # Frontend application
│   ├── components/        # React components
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility libraries
│   ├── pages/             # Page components
│   └── test/              # Frontend tests
├── sql/                   # Database schema files
├── public/                # Static assets
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
└── README.md             # This file
```

## 🔧 Configuration

### Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE legal_analyzer;
CREATE USER legal_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE legal_analyzer TO legal_user;
```

2. Run database initialization:
```bash
curl -X POST http://localhost:8000/init-db
```

### Redis Setup

See `setup_redis.py` for platform-specific instructions:
```bash
python setup_redis.py
```

## 🚀 Deployment

### Using Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment

1. **Backend**: Deploy to any Python-compatible platform (AWS, GCP, Heroku)
2. **Frontend**: Build and deploy to CDN (Vercel, Netlify, AWS S3)
3. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
4. **Redis**: Use managed Redis (AWS ElastiCache, Redis Cloud)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [React](https://reactjs.org/) for the frontend framework
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Google Gemini](https://ai.google.dev/) for AI capabilities
- [Pinecone](https://www.pinecone.io/) for vector database
- [Radix UI](https://www.radix-ui.com/) for accessible UI components

## 📞 Support

If you have any questions or need help, please:
1. Check the [Issues](https://github.com/yourusername/ai-legal-document-analyzer/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about your environment and the issue

---

**⚠️ Disclaimer**: This tool is for informational purposes only and should not be considered as legal advice. Always consult with qualified legal professionals for important legal matters.