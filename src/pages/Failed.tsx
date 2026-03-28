import { useNavigate } from 'react-router-dom';
import { AlertCircle, Trash2, Upload, CheckCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useDocuments } from '@/lib/documents';
import { Button } from '@/components/ui/button';

export default function Failed() {
  const { documents, removeDocument } = useDocuments();
  const navigate = useNavigate();
  const failed = documents.filter(d => d.status === 'failed');

  return (
    <div className="h-full flex flex-col p-6">
      <h1 className="text-2xl font-semibold tracking-tight mb-6 shrink-0">Failed</h1>

      {failed.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <CheckCircle className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="font-medium text-muted-foreground mb-1">No failures</p>
            <p className="text-sm text-muted-foreground/70">All your documents processed successfully</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {failed.map(doc => (
            <div
              key={doc.id}
              className="bg-card rounded-xl border border-border p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 min-w-0">
                  <div className="w-10 h-10 rounded-lg bg-destructive/10 flex items-center justify-center shrink-0 mt-0.5">
                    <AlertCircle className="h-5 w-5 text-destructive" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{doc.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatDistanceToNow(new Date(doc.uploadedAt), { addSuffix: true })}
                    </p>
                    {doc.failureReason && (
                      <p className="text-xs text-destructive mt-2">{doc.failureReason}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={() => removeDocument(doc.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                  <Button size="sm" onClick={() => navigate('/')}>
                    <Upload className="h-4 w-4 mr-1.5" />
                    Re-upload
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
