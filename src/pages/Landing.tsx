import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Scale, Shield, Zap, FileText, MessageSquare, Brain, ArrowRight, BookOpen, Lock } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <AuthSection />
      <Footer />
    </div>
  );
}

function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-[radial-gradient(ellipse_at_center,hsl(210_100%_60%/0.08),transparent_70%)] pointer-events-none" />
      <div className="absolute top-20 right-1/4 w-[400px] h-[400px] bg-[radial-gradient(ellipse_at_center,hsl(260_80%_60%/0.05),transparent_70%)] pointer-events-none" />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between max-w-6xl mx-auto px-6 py-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Scale className="h-4.5 w-4.5 text-primary" />
          </div>
          <span className="font-semibold text-lg tracking-tight text-foreground">LegalMind AI</span>
        </div>
        <div className="flex items-center gap-3">
          <a href="#auth" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Login</a>
          <a href="#auth">
            <Button size="sm" className="rounded-lg">Get Started</Button>
          </a>
        </div>
      </nav>

      {/* Hero content */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 pt-20 pb-28 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/50 text-xs text-muted-foreground mb-8 animate-slide-up">
          <Zap className="h-3 w-3 text-primary" />
          AI-Powered Legal Document Analysis
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.08] mb-6 animate-slide-up" style={{ animationDelay: '100ms' }}>
          Your AI <span className="text-gradient">Legal Assistant</span>
          <br />for smarter decisions
        </h1>

        <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed animate-slide-up" style={{ animationDelay: '200ms' }}>
          Upload legal documents, contracts, and case files. Get instant analysis,
          summaries, and answers — powered by advanced AI.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up" style={{ animationDelay: '300ms' }}>
          <a href="#auth">
            <Button size="lg" className="rounded-xl px-8 h-12 text-base font-medium gap-2">
              Start Free <ArrowRight className="h-4 w-4" />
            </Button>
          </a>
          <a href="#features">
            <Button variant="outline" size="lg" className="rounded-xl px-8 h-12 text-base font-medium">
              Learn More
            </Button>
          </a>
        </div>

        {/* Visual */}
        <div className="mt-16 relative animate-slide-up" style={{ animationDelay: '400ms' }}>
          <div className="glass-card rounded-2xl p-6 max-w-2xl mx-auto glow-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-3 h-3 rounded-full bg-destructive/60" />
              <div className="w-3 h-3 rounded-full bg-[hsl(var(--status-processing))]/60" />
              <div className="w-3 h-3 rounded-full bg-[hsl(var(--status-ready))]/60" />
              <span className="ml-2 text-xs text-muted-foreground">LegalMind AI — Contract Analysis</span>
            </div>
            <div className="space-y-3">
              <div className="flex justify-end">
                <div className="bg-primary/15 text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 text-sm max-w-[70%] text-left text-foreground">
                  What are the termination clauses in this contract?
                </div>
              </div>
              <div className="flex justify-start">
                <div className="bg-card border border-border rounded-2xl rounded-bl-md px-4 py-2.5 text-sm max-w-[85%] text-left">
                  <p className="text-foreground/90 leading-relaxed">Based on Section 8.2, either party may terminate with 30 days written notice. There's also an immediate termination clause for material breach under Section 8.4...</p>
                  <div className="mt-2 px-2.5 py-1.5 rounded-md bg-muted text-xs text-muted-foreground">
                    📄 Page 12, Section 8.2-8.4
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function FeaturesSection() {
  const features = [
    {
      icon: FileText,
      title: 'Document Intelligence',
      desc: 'Upload contracts, briefs, case files, and legal memos. Our AI processes and indexes every page instantly.',
    },
    {
      icon: MessageSquare,
      title: 'Conversational Analysis',
      desc: 'Ask natural language questions about your documents. Get precise answers with page citations.',
    },
    {
      icon: Brain,
      title: 'Deep Legal Reasoning',
      desc: 'Toggle between quick answers and deep agentic analysis for complex legal questions.',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      desc: 'Your documents are encrypted and processed securely. SOC 2 compliant infrastructure.',
    },
    {
      icon: BookOpen,
      title: 'Case Law References',
      desc: 'Automatic cross-referencing with relevant case law and statutory provisions.',
    },
    {
      icon: Lock,
      title: 'Confidential & Private',
      desc: 'No data is used for training. Your legal documents remain strictly confidential.',
    },
  ];

  return (
    <section id="features" className="relative py-24 px-6">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,hsl(210_100%_60%/0.04),transparent_70%)] pointer-events-none" />
      <div className="relative max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">Built for legal professionals</h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">Everything you need to analyze legal documents faster and smarter.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <div key={i} className="group glass-card rounded-xl p-6 hover:border-primary/30 transition-all duration-300">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/15 transition-colors">
                <f.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  const steps = [
    { num: '01', title: 'Upload', desc: 'Drop your legal document — PDF, DOCX, or TXT.' },
    { num: '02', title: 'Process', desc: 'AI indexes, analyzes, and structures the content.' },
    { num: '03', title: 'Chat', desc: 'Ask questions and get cited, accurate answers.' },
  ];

  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">How it works</h2>
          <p className="text-muted-foreground text-lg">Three simple steps to legal document intelligence.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((s, i) => (
            <div key={i} className="text-center">
              <div className="text-5xl font-bold text-primary/20 mb-3">{s.num}</div>
              <h3 className="font-semibold text-lg mb-2">{s.title}</h3>
              <p className="text-sm text-muted-foreground">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AuthSection() {
  const [mode, setMode] = useState<'login' | 'signup'>('signup');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login, signup, user, isLoading } = useAuth();
  const navigate = useNavigate();

  // If the user becomes authenticated, redirect to the app.
  if (!isLoading && user) {
    navigate('/', { replace: true });
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await signup(email, password, name);
      }
      navigate('/', { replace: true });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Authentication failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="auth" className="py-24 px-6 border-t border-border">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold tracking-tight mb-2">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p className="text-sm text-muted-foreground">
            {mode === 'login' ? 'Sign in to access your documents' : 'Start analyzing legal documents with AI'}
          </p>
        </div>

        <div className="glass-card rounded-2xl p-8 glow-border">
          {/* Mode toggle */}
          <div className="flex items-center rounded-xl bg-muted p-1 mb-6">
            <button
              onClick={() => setMode('signup')}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${mode === 'signup' ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Sign Up
            </button>
            <button
              onClick={() => setMode('login')}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${mode === 'login' ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              Login
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Full Name</label>
                <Input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="John Doe"
                  required
                  className="h-11 rounded-xl bg-muted border-border focus:border-primary"
                />
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Email</label>
              <Input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@lawfirm.com"
                required
                className="h-11 rounded-xl bg-muted border-border focus:border-primary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Password</label>
              <Input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={6}
                className="h-11 rounded-xl bg-muted border-border focus:border-primary"
              />
            </div>
            {error ? (
              <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl p-3">
                {error}
              </div>
            ) : null}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-xl text-sm font-medium mt-2"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                </span>
              ) : (
                mode === 'login' ? 'Sign In' : 'Create Account'
              )}
            </Button>
          </form>
        </div>

        <p className="text-center text-xs text-muted-foreground mt-6">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border py-8 px-6">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-foreground">LegalMind AI</span>
        </div>
        <p className="text-xs text-muted-foreground">© 2026 LegalMind AI. All rights reserved.</p>
      </div>
    </footer>
  );
}
