import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, PanelRight, MoreHorizontal, FileText, Trash2, Upload } from 'lucide-react';
import { useDocuments } from '@/lib/documents';
import { StatusBadge } from '@/components/documents/StatusBadge';
import { ChatArea } from '@/components/chat/ChatArea';
import { ContextPanel } from '@/components/chat/ContextPanel';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

export default function DocumentWorkspace() {
  const { docId } = useParams<{ docId: string }>();
  const { documents, getMessages, removeDocument } = useDocuments();
  const navigate = useNavigate();
  const [contextOpen, setContextOpen] = useState(true);

  const doc = documents.find(d => d.id === docId);
  const messages = docId ? getMessages(docId) : [];

  if (!doc) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <FileText className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
          <h2 className="text-lg font-medium mb-1">Document not found</h2>
          <p className="text-sm text-muted-foreground mb-4">This document may have been deleted.</p>
          <Button variant="outline" onClick={() => navigate('/documents')}>View all documents</Button>
        </div>
      </div>
    );
  }

  // Processing state
  if (doc.status === 'uploaded' || doc.status === 'indexed' || doc.status === 'analyzing') {
    const stageLabel =
      doc.status === 'uploaded'
        ? 'Upload received'
        : doc.status === 'indexed'
          ? 'Indexing'
          : 'Analyzing';
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center max-w-sm">
          <Loader2 className="h-12 w-12 text-muted-foreground mx-auto mb-6 animate-spin" />
          <h2 className="text-lg font-semibold mb-2">{doc.name}</h2>
          <p className="text-sm text-muted-foreground mb-4">Processing your document...</p>
          <div className="flex items-center justify-center gap-2">
            <span className="w-2 h-2 rounded-full badge-processing" />
            <span className="text-sm text-muted-foreground">{doc.processingStage || stageLabel}</span>
          </div>
          <p className="text-xs text-muted-foreground/60 mt-6">
            This usually takes a few moments. The workspace will open automatically when ready.
          </p>
        </div>
      </div>
    );
  }

  // Failed state
  if (doc.status === 'failed') {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center max-w-sm">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-6" />
          <h2 className="text-lg font-semibold mb-2">{doc.name}</h2>
          <p className="text-sm text-muted-foreground mb-2">Processing failed</p>
          <p className="text-sm text-muted-foreground/80 mb-6">{doc.failureReason}</p>
          <div className="flex gap-3 justify-center">
            <Button
              variant="outline"
              onClick={() => {
                removeDocument(doc.id);
                navigate('/documents');
              }}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
            <Button onClick={() => navigate('/')}>
              <Upload className="h-4 w-4 mr-2" />
              Re-upload
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Ready state — full workspace
  return (
    <div className="h-full flex">
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="h-14 border-b border-border bg-card flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <h1 className="font-medium text-sm truncate">{doc.name}</h1>
            <StatusBadge status={doc.status} />
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className={cn('h-8 w-8 hidden lg:flex', contextOpen && 'bg-accent')}
              onClick={() => setContextOpen(!contextOpen)}
            >
              <PanelRight className="h-4 w-4" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setContextOpen(true)}>
                  View Summary
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => {
                    removeDocument(doc.id);
                    navigate('/documents');
                  }}
                >
                  Delete Document
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Chat */}
        <ChatArea messages={messages} docId={doc.id} />
      </div>

      {/* Context Panel */}
      {contextOpen && <ContextPanel doc={doc} messages={messages} />}
    </div>
  );
}
