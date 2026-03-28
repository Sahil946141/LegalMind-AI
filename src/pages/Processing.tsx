import { useNavigate } from 'react-router-dom';
import { Clock, Loader2, CheckCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useDocuments } from '@/lib/documents';
import { Button } from '@/components/ui/button';

export default function Processing() {
  const { documents } = useDocuments();
  const navigate = useNavigate();
  const processing = documents.filter(
    d => d.status === 'uploaded' || d.status === 'indexed' || d.status === 'analyzing'
  );

  return (
    <div className="h-full flex flex-col p-6">
      <h1 className="text-2xl font-semibold tracking-tight mb-6 shrink-0">Processing</h1>

      {processing.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <CheckCircle className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="font-medium text-muted-foreground mb-1">All caught up</p>
            <p className="text-sm text-muted-foreground/70">No documents are currently being processed</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {processing.map(doc => (
            <div
              key={doc.id}
              className="bg-card rounded-xl border border-border p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center shrink-0">
                  <Loader2 className="h-5 w-5 text-muted-foreground animate-spin" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{doc.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(doc.uploadedAt), { addSuffix: true })}
                    </span>
                    <span className="text-xs text-muted-foreground">·</span>
                    <span className="text-xs badge-processing px-1.5 py-0.5 rounded-full">
                      {doc.processingStage || (doc.status === 'uploaded' ? 'Upload received' : doc.status === 'indexed' ? 'Indexing' : 'Analyzing')}
                    </span>
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate(`/documents/${doc.id}`)}
              >
                Open
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
