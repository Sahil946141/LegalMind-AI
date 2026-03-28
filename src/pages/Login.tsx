import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Scale } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login, user, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && user) {
      navigate('/', { replace: true });
    }
  }, [isLoading, navigate, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      // Use replace to avoid bouncing back to /login via history.
      navigate('/', { replace: true });
      // Fallback for rare router/state race conditions.
      setTimeout(() => {
        if (window.location.pathname === '/login') window.location.assign('/');
      }, 0);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Sign in failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-[radial-gradient(ellipse_at_center,hsl(210_100%_60%/0.06),transparent_70%)] pointer-events-none" />

      <div className="w-full max-w-sm relative">
        <div className="text-center mb-8">
          <Link to="/landing" className="inline-flex items-center gap-2.5 mb-6">
            <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
              <Scale className="h-5 w-5 text-primary" />
            </div>
            <span className="font-semibold text-xl tracking-tight">LegalMind AI</span>
          </Link>
          <h1 className="text-2xl font-bold tracking-tight mb-1.5">Welcome back</h1>
          <p className="text-sm text-muted-foreground">Sign in to continue</p>
        </div>

        <div className="glass-card rounded-2xl p-7 glow-border">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Email</label>
              <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@lawfirm.com" required className="h-11 rounded-xl bg-muted border-border" />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Password</label>
              <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required className="h-11 rounded-xl bg-muted border-border" />
            </div>
            {error ? (
              <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-xl p-3">
                {error}
              </div>
            ) : null}
            <Button type="submit" disabled={loading} className="w-full h-11 rounded-xl font-medium mt-1">
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-muted-foreground mt-5">
          Don't have an account? <Link to="/signup" className="text-primary hover:underline font-medium">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
