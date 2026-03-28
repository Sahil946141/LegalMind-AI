import { cn } from '@/lib/utils';
import type { DocStatus } from '@/lib/documents';

const config: Record<DocStatus, { label: string; className: string }> = {
  ready: { label: 'Ready', className: 'badge-ready' },
  uploaded: { label: 'Uploaded', className: 'badge-processing' },
  indexed: { label: 'Indexing', className: 'badge-processing' },
  analyzing: { label: 'Analyzing', className: 'badge-processing' },
  failed: { label: 'Failed', className: 'badge-failed' },
};

export function StatusBadge({ status }: { status: DocStatus }) {
  const { label, className } = config[status];
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', className)}>
      {(status === 'uploaded' || status === 'indexed' || status === 'analyzing') && (
        <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 animate-pulse" />
      )}
      {label}
    </span>
  );
}
