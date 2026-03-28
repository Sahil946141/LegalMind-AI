-- Create documents and related tables
-- Run this after auth_schema.sql

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    doc_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- Document analysis table
CREATE TABLE IF NOT EXISTS doc_analysis (
    doc_id TEXT PRIMARY KEY,
    clause_analysis_json JSONB,
    read_more_cache TEXT,
    page_wise_cache JSONB,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);

-- QnA logs table
CREATE TABLE IF NOT EXISTS qna_logs (
    qna_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    mode TEXT NOT NULL,
    rewrite_used BOOLEAN DEFAULT FALSE,
    used_model TEXT,
    best_score DOUBLE PRECISION,
    latency_ms INTEGER,
    citations_json JSONB,
    status TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- QnA feedback table
CREATE TABLE IF NOT EXISTS qna_feedback (
    feedback_id SERIAL PRIMARY KEY,
    qna_id TEXT,
    user_id TEXT,
    doc_id TEXT,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for QnA tables
CREATE INDEX IF NOT EXISTS idx_qna_logs_user_doc ON qna_logs(user_id, doc_id);
CREATE INDEX IF NOT EXISTS idx_qna_feedback_qna_id ON qna_feedback(qna_id);