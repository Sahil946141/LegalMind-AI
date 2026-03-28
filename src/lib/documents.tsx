import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { apiClient } from './api';
import { useAuth } from './auth';

export type DocStatus = 'uploaded' | 'indexed' | 'analyzing' | 'ready' | 'failed';

export type ChatMode = 'basic' | 'agentic';

export type Citation = {
  filename?: string | null;
  page?: number | null;
  chunk_index?: number | null;
  score?: number | null;
};

export interface Document {
  id: string;
  name: string;
  uploadedAt: string;
  status: DocStatus;
  pages?: number;
  summary?: string;
  failureReason?: string;
  processingStage?: string;
  fileType: string;
  qna_ready?: boolean;
  analysis_ready?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
}

interface DocumentContextValue {
  documents: Document[];
  messages: Record<string, ChatMessage[]>;
  addDocument: (file: File) => Promise<Document>;
  removeDocument: (id: string) => Promise<void>;
  addMessage: (docId: string, role: 'user' | 'assistant', content: string, citations?: Citation[]) => void;
  getMessages: (docId: string) => ChatMessage[];
  refreshDocuments: () => Promise<void>;
  askQuestion: (docId: string, question: string, mode: ChatMode) => Promise<void>;
}

const DocumentContext = createContext<DocumentContextValue | null>(null);

export function DocumentProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messagesState, setMessages] = useState<Record<string, ChatMessage[]>>({});
  const { user, isLoading } = useAuth();

  // Load documents from API only when user is authenticated
  useEffect(() => {
    if (!isLoading && user) {
      refreshDocuments();
    } else if (!isLoading && !user) {
      // Clear documents when user logs out
      setDocuments([]);
      setMessages({});
    }
  }, [user, isLoading]);

  const refreshDocuments = useCallback(async () => {
    // Don't try to fetch documents if user is not authenticated
    if (!user) {
      setDocuments([]);
      return;
    }

    try {
      const response = await apiClient.getDocuments();
      const docs = response.documents.map((doc: any) => ({
        id: doc.doc_id,
        name: doc.doc_name,
        uploadedAt: doc.created_at || new Date().toISOString(),
        status: doc.status as DocStatus,
        pages: doc.pages,
        summary: doc.summary,
        failureReason: doc.error_message,
        fileType: doc.doc_name.split('.').pop()?.toUpperCase() || 'PDF',
        qna_ready: doc.qna_ready,
        analysis_ready: doc.analysis_ready,
      }));
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
      // Keep existing documents on error
    }
  }, [user]);

  const isInProgressStatus = useCallback((status: DocStatus) => {
    return status === 'uploaded' || status === 'indexed' || status === 'analyzing';
  }, []);

  const pollDocumentUntilDone = useCallback(
    async (docId: string, fileNameForWelcome?: string) => {
      const tick = async (): Promise<void> => {
        try {
          const statusRes = await apiClient.getDocumentStatus(docId);
          const nextStatus = statusRes.status as DocStatus;
          const errorMessage = statusRes.error_message as string | undefined;

          setDocuments(prev =>
            prev.map(d =>
              d.id === docId
                ? {
                    ...d,
                    status: nextStatus,
                    failureReason: errorMessage,
                  }
                : d
            )
          );

          if (nextStatus === 'ready') {
            if (fileNameForWelcome) {
              setMessages(prev => ({
                ...prev,
                [docId]: [
                  {
                    id: self.crypto?.randomUUID?.() || Math.random().toString(36).substring(2, 15),
                    role: 'assistant',
                    content: `I've finished analyzing "${fileNameForWelcome}". Feel free to ask me anything about this document.`,
                    timestamp: new Date().toISOString(),
                  },
                ],
              }));
            }
            // Sync list for other UI surfaces
            await refreshDocuments();
            return;
          }

          if (nextStatus === 'failed') {
            await refreshDocuments();
            return;
          }

          if (isInProgressStatus(nextStatus)) {
            setTimeout(tick, 2500);
            return;
          }

          // Unknown/unexpected: stop polling but keep list refreshed
          await refreshDocuments();
        } catch (error) {
          console.error('Failed to poll document status:', error);
          setTimeout(tick, 4000);
        }
      };

      // start
      setTimeout(tick, 1200);
    },
    [isInProgressStatus, refreshDocuments]
  );

  const addDocument = useCallback(async (file: File): Promise<Document> => {
    try {
      const response = await apiClient.uploadFile(file);
      
      const doc: Document = {
        id: response.doc_id,
        name: response.doc_name,
        uploadedAt: new Date().toISOString(),
        status: response.status as DocStatus,
        fileType: file.name.split('.').pop()?.toUpperCase() || 'PDF',
        qna_ready: response.qna_ready,
        analysis_ready: response.analysis_ready,
      };

      setDocuments(prev => [doc, ...prev]);
      setMessages(prev => ({ ...prev, [doc.id]: [] }));

      // Poll this doc until it becomes ready/failed
      pollDocumentUntilDone(doc.id, file.name);

      return doc;
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    }
  }, [pollDocumentUntilDone]);

  const removeDocument = useCallback(async (id: string) => {
    try {
      await apiClient.deleteDocument(id);
      setDocuments(prev => prev.filter(d => d.id !== id));
      setMessages(prev => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } catch (error) {
      console.error('Failed to delete document:', error);
      throw error;
    }
  }, []);

  const addMessage = useCallback(
    (docId: string, role: 'user' | 'assistant', content: string, citations?: Citation[]) => {
      const msg: ChatMessage = {
        id: self.crypto?.randomUUID?.() || Math.random().toString(36).substring(2, 15),
        role,
        content,
        citations,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => ({
        ...prev,
        [docId]: [...(prev[docId] || []), msg],
      }));
    },
    []
  );

  const askQuestion = useCallback(async (docId: string, question: string, mode: ChatMode) => {
    // Add user message
    addMessage(docId, 'user', question);

    try {
      const response =
        mode === 'agentic'
          ? await apiClient.askQuestionAgentic(docId, question)
          : await apiClient.askQuestion(docId, question);
      
      // Add assistant response
      addMessage(docId, 'assistant', response.answer, response.citations);
    } catch (error) {
      console.error('Failed to ask question:', error);
      const message = error instanceof Error ? error.message : 'Request failed';
      addMessage(docId, 'assistant', message);
    }
  }, [addMessage]);

  const getMessages = useCallback(
    (docId: string): ChatMessage[] => messagesState[docId] || [],
    [messagesState]
  );

  return (
    <DocumentContext.Provider value={{ 
      documents, 
      messages: messagesState, 
      addDocument, 
      removeDocument, 
      addMessage, 
      getMessages, 
      refreshDocuments,
      askQuestion 
    }}>
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocuments() {
  const ctx = useContext(DocumentContext);
  if (!ctx) throw new Error('useDocuments must be used within DocumentProvider');
  return ctx;
}