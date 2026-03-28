// API configuration and utilities
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get auth token from localStorage
const getAuthToken = (): string | null => {
  const user = localStorage.getItem('docuchat_user');
  if (user) {
    try {
      const userData = JSON.parse(user);
      return userData.token; // We'll need to store the JWT token
    } catch {
      return null;
    }
  }
  return null;
};

// API client with auth headers
export const apiClient = {
  async parseError(response: Response): Promise<string> {
    const fallback = `Request failed (${response.status})`;
    const data = await response.json().catch(() => null);

    if (!data) return fallback;

    const detail = (data as any).detail;
    const message = (data as any).message;

    if (typeof detail === 'string' && detail.trim()) return detail;
    if (typeof message === 'string' && message.trim()) return message;

    // FastAPI validation errors are often arrays of objects
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0];
      if (first?.msg) return String(first.msg);
      return JSON.stringify(detail);
    }

    // Some endpoints return dict detail (e.g. 409 status conflicts)
    if (detail && typeof detail === 'object') {
      if ((detail as any).message) return String((detail as any).message);
      return JSON.stringify(detail);
    }

    if ((data as any).error) return String((data as any).error);
    return fallback;
  },

  async request(endpoint: string, options: RequestInit = {}) {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    };

    // Add auth header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async uploadFile(file: File) {
    const token = getAuthToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async getDocuments() {
    return this.request('/documents');
  },

  async getDocumentStatus(docId: string) {
    return this.request(`/documents/${docId}/status`);
  },

  async deleteDocument(docId: string) {
    return this.request(`/documents/${docId}`, { method: 'DELETE' });
  },

  async askQuestion(docId: string, question: string, topK: number = 5) {
    const formData = new FormData();
    formData.append('doc_id', docId);
    formData.append('question', question);
    formData.append('top_k', topK.toString());

    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/qna`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async askQuestionAgentic(docId: string, question: string) {
    const formData = new FormData();
    formData.append('doc_id', docId);
    formData.append('question', question);

    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/qna/agentic`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async readMore(docId: string) {
    const formData = new FormData();
    formData.append('doc_id', docId);
    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/read_more`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async pageWise(docId: string) {
    const formData = new FormData();
    formData.append('doc_id', docId);
    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}/page_wise`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async signup(email: string, password: string, name: string) {
    // Backend supports JSON signup at /auth/signup. (Form-data register exists at /auth/register.)
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    if (!response.ok) {
      const errorMessage = await this.parseError(response);
      throw new Error(errorMessage);
    }

    return response.json();
  },

  async me() {
    return this.request('/auth/me');
  },
};