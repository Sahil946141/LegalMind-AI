import { useState, useRef, DragEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDocuments } from '@/lib/documents';

export function UploadCard() {
  const [isDragging, setIsDragging] = useState(false);
  const { addDocument } = useDocuments();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList) => {
    try {
      const uploadPromises = Array.from(files).map(file => addDocument(file));
      const docs = await Promise.all(uploadPromises);
      
      if (docs.length === 1) {
        navigate(`/documents/${docs[0].id}`);
      } else {
        navigate('/documents');
      }
    } catch (error) {
      console.error('Upload failed:', error);
      // You might want to show an error toast here
    }
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer?.files?.length) await handleFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      className={cn(
        'border-2 border-dashed rounded-2xl p-16 text-center cursor-pointer transition-all duration-200',
        isDragging
          ? 'border-primary bg-primary/5 scale-[1.01] glow-border'
          : 'border-border hover:border-muted-foreground/30 hover:bg-muted/20'
      )}
    >
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        multiple
        accept=".pdf,.docx,.doc,.txt"
        onChange={async e => e.target.files?.length && await handleFiles(e.target.files)}
      />
      <div className="flex flex-col items-center">
        {isDragging ? (
          <div className="w-14 h-14 rounded-2xl bg-primary/15 flex items-center justify-center mb-4">
            <FileUp className="h-7 w-7 text-primary" />
          </div>
        ) : (
          <div className="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center mb-4">
            <Upload className="h-7 w-7 text-muted-foreground" />
          </div>
        )}
        <p className="font-medium text-foreground mb-1">
          {isDragging ? 'Drop files here' : 'Drop files here or click to browse'}
        </p>
        <p className="text-sm text-muted-foreground">
          Supports PDF, DOCX, TXT — up to 50MB
        </p>
      </div>
    </div>
  );
}
