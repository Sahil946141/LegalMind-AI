import { useMemo, useState } from 'react';
import { FileText, Calendar, Layers, BookOpen, Scale } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { apiClient } from '@/lib/api';
import type { Document, ChatMessage } from '@/lib/documents';
import { Button } from '@/components/ui/button';

interface ContextPanelProps {
  doc: Document;
  messages: ChatMessage[];
}

export function ContextPanel({ doc, messages }: ContextPanelProps) {
  const citations = useMemo(
    () => messages.filter(m => m.role === 'assistant' && m.citations?.length).flatMap(m => m.citations!),
    [messages]
  );

  const [readMoreText, setReadMoreText] = useState<string | null>(null);
  const [pageWise, setPageWise] = useState<any[] | null>(null);
  const [loadingReadMore, setLoadingReadMore] = useState(false);
  const [loadingPageWise, setLoadingPageWise] = useState(false);
  const [panelError, setPanelError] = useState<string | null>(null);

  return (
    <div className="w-80 border-l border-border bg-card/50 overflow-y-auto hidden lg:block shrink-0">
      <div className="p-6 space-y-6">
        {/* Summary */}
        <section>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
            <BookOpen className="h-3.5 w-3.5" />
            Summary
          </h3>
          <p className="text-sm leading-relaxed text-foreground/80">
            {readMoreText || doc.summary || 'Load “Read more” once the document is ready.'}
          </p>
          <div className="mt-3 flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={loadingReadMore || doc.status !== 'ready'}
              onClick={async () => {
                setPanelError(null);
                setLoadingReadMore(true);
                try {
                  const res = await apiClient.readMore(doc.id);
                  setReadMoreText(res.explanation || null);
                } catch (e) {
                  setPanelError(e instanceof Error ? e.message : 'Failed to load read more');
                } finally {
                  setLoadingReadMore(false);
                }
              }}
            >
              {loadingReadMore ? 'Loading…' : 'Read more'}
            </Button>
          </div>
        </section>

        {/* Details */}
        <section>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
            <Scale className="h-3.5 w-3.5" />
            Document Info
          </h3>
          <div className="space-y-3 bg-muted/30 rounded-xl p-4">
            <DetailRow icon={<Layers className="h-3.5 w-3.5" />} label="Pages" value={doc.pages ? `${doc.pages} pages` : '—'} />
            <DetailRow icon={<Calendar className="h-3.5 w-3.5" />} label="Uploaded" value={formatDistanceToNow(new Date(doc.uploadedAt), { addSuffix: true })} />
            <DetailRow icon={<FileText className="h-3.5 w-3.5" />} label="Format" value={doc.fileType} />
          </div>
        </section>

        {/* Page-wise */}
        <section>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Page-wise
          </h3>
          <div className="flex gap-2 mb-3">
            <Button
              size="sm"
              variant="outline"
              disabled={loadingPageWise || doc.status !== 'ready'}
              onClick={async () => {
                setPanelError(null);
                setLoadingPageWise(true);
                try {
                  const res = await apiClient.pageWise(doc.id);
                  setPageWise(res.pages || []);
                } catch (e) {
                  setPanelError(e instanceof Error ? e.message : 'Failed to load page-wise');
                } finally {
                  setLoadingPageWise(false);
                }
              }}
            >
              {loadingPageWise ? 'Loading…' : 'Load page-wise'}
            </Button>
          </div>
          {pageWise?.length ? (
            <div className="space-y-2">
              {pageWise.slice(0, 8).map((p, i) => (
                <div key={i} className="text-xs p-3 bg-muted/30 rounded-lg border border-border/50">
                  <div className="font-semibold text-foreground/80">{p.location}</div>
                  {p.main_topics?.length ? (
                    <div className="mt-1 text-muted-foreground">Topics: {p.main_topics.join(', ')}</div>
                  ) : null}
                  {p.key_risks?.length ? (
                    <div className="mt-1 text-muted-foreground">Risks: {p.key_risks.join(', ')}</div>
                  ) : null}
                </div>
              ))}
              {pageWise.length > 8 ? (
                <div className="text-xs text-muted-foreground/70">Showing 8 of {pageWise.length} pages</div>
              ) : null}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground/70">
              {doc.status === 'ready' ? 'Load page-wise analysis to see topics/risks by page.' : 'Available when the document is ready.'}
            </p>
          )}
        </section>

        {panelError ? (
          <div className="text-xs text-destructive bg-destructive/10 border border-destructive/20 rounded-lg p-3">
            {panelError}
          </div>
        ) : null}

        {/* Citations */}
        {citations.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Sources & Citations
            </h3>
            <div className="space-y-2">
              {citations.map((c, i) => (
                <div key={i} className="text-sm p-3 bg-muted/30 rounded-lg border border-border/50">
                  <span className="text-xs font-semibold text-primary/70">
                    📄 {c.filename ? `${c.filename} · ` : ''}Page {c.page ?? '—'}
                  </span>
                  <p className="mt-1 text-foreground/70 leading-relaxed text-xs">
                    {typeof c.chunk_index === 'number' ? `Chunk ${c.chunk_index}` : 'Source'}
                    {typeof c.score === 'number' ? ` · score ${c.score.toFixed(3)}` : ''}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

function DetailRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="flex items-center gap-2 text-muted-foreground">
        {icon}
        {label}
      </span>
      <span className="text-foreground/80 font-medium">{value}</span>
    </div>
  );
}
