import { Input } from '@/components/ui/input';
import { useAuth } from '@/lib/auth';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold tracking-tight mb-8">Settings</h1>

        <div className="space-y-8">
          {/* Profile */}
          <section>
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Profile</h2>
            <div className="bg-card rounded-xl border border-border p-5 space-y-4">
              <div className="flex items-center gap-4 mb-2">
                <div className="w-12 h-12 rounded-full bg-primary/15 flex items-center justify-center text-lg font-semibold text-primary">
                  {user?.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="font-medium">{user?.name}</p>
                  <p className="text-sm text-muted-foreground">{user?.email}</p>
                </div>
              </div>
            </div>
          </section>

          {/* Workspace */}
          <section>
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Workspace</h2>
            <div className="bg-card rounded-xl border border-border p-5 space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Workspace Name</label>
                <Input defaultValue="My Legal Workspace" className="mt-1.5 max-w-sm bg-muted border-border" />
              </div>
            </div>
          </section>

          {/* Preferences */}
          <section>
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Chat Preferences</h2>
            <div className="bg-card rounded-xl border border-border p-5 space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Default Analysis Mode</label>
                <p className="text-xs text-muted-foreground mt-0.5 mb-2">Choose the default mode for new conversations</p>
                <div className="flex items-center rounded-xl bg-muted p-1 w-fit">
                  <button className="px-4 py-2 rounded-lg text-sm font-medium bg-card shadow-sm text-foreground">Quick</button>
                  <button className="px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Deep</button>
                </div>
              </div>
            </div>
          </section>

          {/* About */}
          <section>
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">About</h2>
            <div className="bg-card rounded-xl border border-border p-5">
              <p className="text-sm font-medium">LegalMind AI</p>
              <p className="text-xs text-muted-foreground mt-1">Version 1.0.0 · AI-powered legal document intelligence</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
