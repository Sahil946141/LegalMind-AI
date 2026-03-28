import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Search, Trash2, Upload, FolderOpen } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useDocuments } from '@/lib/documents';
import { StatusBadge } from '@/components/documents/StatusBadge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function Documents() {
  const { documents, removeDocument } = useDocuments();
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const filtered = documents.filter(d =>
    d.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 shrink-0">
        <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
        <Button onClick={() => navigate('/')} size="sm">
          <Upload className="h-4 w-4 mr-2" />
          Upload
        </Button>
      </div>

      {/* Search */}
      <div className="mb-4 shrink-0">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <FolderOpen className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="font-medium text-muted-foreground mb-1">
              {search ? 'No documents match your search' : 'No documents yet'}
            </p>
            <p className="text-sm text-muted-foreground/70">
              {search ? 'Try a different search term' : 'Upload a document to get started'}
            </p>
          </div>
        ) : (
          <div className="bg-card rounded-xl border border-border divide-y divide-border">
            {filtered.map(doc => (
              <div
                key={doc.id}
                onClick={() => navigate(`/documents/${doc.id}`)}
                className="flex items-center justify-between px-4 py-3.5 hover:bg-accent/40 cursor-pointer transition-colors group"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{doc.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(doc.uploadedAt), { addSuffix: true })}
                      {doc.pages && ` · ${doc.pages} pages`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <StatusBadge status={doc.status} />
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      removeDocument(doc.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-muted transition-all"
                    title="Delete document"
                  >
                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
