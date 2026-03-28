import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Zap, Scale } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDocuments, type ChatMessage } from '@/lib/documents';
import { Button } from '@/components/ui/button';

const suggestions = [
  { text: 'Summarize this document', icon: '📋' },
  { text: 'What are the key legal clauses?', icon: '⚖️' },
  { text: 'Identify potential risks', icon: '⚠️' },
  { text: 'List all parties involved', icon: '👥' },
];

interface ChatAreaProps {
  messages: ChatMessage[];
  docId: string;
}

export function ChatArea({ messages, docId }: ChatAreaProps) {
  const { askQuestion } = useDocuments();
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<'basic' | 'deep'>('basic');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);

  const handleSend = async (text?: string) => {
    const content = text || input.trim();
    if (!content || isTyping) return;
    setInput('');
    setIsTyping(true);

    try {
      await askQuestion(docId, content, mode === 'deep' ? 'agentic' : 'basic');
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-6 space-y-6">
          {messages.length === 0 && !isTyping ? (
            <div className="flex items-center justify-center pt-16 sm:pt-24">
              <div className="text-center max-w-lg">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                  <Scale className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Start your analysis</h2>
                <p className="text-sm text-muted-foreground mb-8">Ask questions about this legal document. Get precise, cited answers.</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md mx-auto">
                  {suggestions.map(s => (
                    <button
                      key={s.text}
                      onClick={() => handleSend(s.text)}
                      className="text-left text-sm p-4 rounded-xl border border-border bg-card/50 hover:bg-accent hover:border-primary/20 transition-all duration-200 group"
                    >
                      <span className="text-lg mb-1.5 block">{s.icon}</span>
                      <span className="text-foreground/80 group-hover:text-foreground transition-colors">{s.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map(msg => (
                <div
                  key={msg.id}
                  className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}
                >
                  <div
                    className={cn(
                      'max-w-[80%] rounded-2xl px-4 py-3',
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-br-lg'
                        : 'bg-card border border-border rounded-bl-lg'
                    )}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    {msg.citations?.map((c, i) => (
                      <div key={i} className="mt-3 text-xs p-3 rounded-lg bg-muted/50 border border-border/50">
                        <span className="font-semibold text-primary/70">
                          📄 {c.filename ? `${c.filename} · ` : ''}Page {c.page ?? '—'}
                        </span>
                        <p className="mt-1 text-foreground/70 leading-relaxed">
                          {typeof c.chunk_index === 'number' ? `Chunk ${c.chunk_index}` : 'Source'}
                          {typeof c.score === 'number' ? ` · score ${c.score.toFixed(3)}` : ''}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-card border border-border rounded-2xl rounded-bl-lg px-5 py-4">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-background/80 backdrop-blur-sm p-4 shrink-0">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-3 bg-card rounded-2xl border border-border p-2 pl-4 glow-border">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask anything about this document..."
              rows={1}
              className="flex-1 resize-none bg-transparent py-2.5 text-sm placeholder:text-muted-foreground/60 focus:outline-none"
            />
            <div className="flex items-center gap-1.5 shrink-0 pb-0.5">
              {/* Mode toggle */}
              <div className="flex items-center rounded-lg bg-muted p-0.5">
                <button
                  onClick={() => setMode('basic')}
                  className={cn(
                    'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all',
                    mode === 'basic' ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Zap className="h-3 w-3" />
                  Quick
                </button>
                <button
                  onClick={() => setMode('deep')}
                  className={cn(
                    'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all',
                    mode === 'deep' ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Sparkles className="h-3 w-3" />
                  Deep
                </button>
              </div>
              <Button
                onClick={() => handleSend()}
                size="icon"
                disabled={!input.trim() && !isTyping}
                className="rounded-xl h-9 w-9 shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground/50 text-center mt-2">
            AI can make mistakes. Always verify legal advice with a qualified attorney.
          </p>
        </div>
      </div>
    </div>
  );
}
