import { useNavigate } from 'react-router-dom';
import { FileText, Scale } from 'lucide-react';
import { useDocuments } from '@/lib/documents';
import { UploadCard } from '@/components/documents/UploadCard';
import { StatusBadge } from '@/components/documents/StatusBadge';

const Index = () => {
  const { documents } = useDocuments();
  const navigate = useNavigate();
  const recentReady = documents.filter(d => d.status === 'ready').slice(0, 4);

  return (
    <div className="h-full flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        {documents.length === 0 ? (
          <>
            <div className="text-center mb-10">
              <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5">
                <Scale className="h-7 w-7 text-primary" />
              </div>
              <h1 className="text-3xl font-bold tracking-tight mb-2">Welcome to LegalMind</h1>
              <p className="text-muted-foreground">Upload a legal document to start your AI-powered analysis</p>
            </div>
            <UploadCard />
            <div className="mt-6 flex items-center justify-center gap-4 text-xs text-muted-foreground">
              <span className="px-2.5 py-1 rounded-lg bg-muted font-medium">PDF</span>
              <span className="px-2.5 py-1 rounded-lg bg-muted font-medium">DOCX</span>
              <span className="px-2.5 py-1 rounded-lg bg-muted font-medium">TXT</span>
              <span className="text-muted-foreground/50">Up to 50MB</span>
            </div>
          </>
        ) : (
          <>
            <div className="mb-8">
              <h1 className="text-2xl font-bold tracking-tight mb-1">Upload a document</h1>
              <p className="text-sm text-muted-foreground">Drop a file to start your legal analysis</p>
            </div>
            <UploadCard />
            {recentReady.length > 0 && (
              <div className="mt-10">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-medium text-muted-foreground">Recent Documents</h2>
                  <button onClick={() => navigate('/documents')} className="text-xs text-primary font-medium hover:underline">View all</button>
                </div>
                <div className="bg-card rounded-xl border border-border divide-y divide-border">
                  {recentReady.map(doc => (
                    <button
                      key={doc.id}
                      onClick={() => navigate(`/documents/${doc.id}`)}
                      className="w-full flex items-center gap-3 px-4 py-3.5 hover:bg-accent/50 text-left transition-colors first:rounded-t-xl last:rounded-b-xl"
                    >
                      <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                      <span className="text-sm font-medium truncate flex-1">{doc.name}</span>
                      <StatusBadge status={doc.status} />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Index;
