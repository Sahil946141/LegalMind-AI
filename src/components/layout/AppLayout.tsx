import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Menu, Scale } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AppSidebar } from './AppSidebar';

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-background/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:relative z-50 h-full border-r border-border transition-all duration-200 ease-in-out shrink-0',
          collapsed ? 'lg:w-16' : 'lg:w-60',
          mobileOpen ? 'w-60 translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <AppSidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
          onClose={() => setMobileOpen(false)}
        />
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <header className="h-14 border-b border-border flex items-center px-4 lg:hidden bg-card/50 backdrop-blur-sm">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 -ml-2 rounded-lg hover:bg-muted transition-colors"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="ml-3 flex items-center gap-2">
            <Scale className="h-4 w-4 text-primary" />
            <span className="font-semibold">LegalMind</span>
          </div>
        </header>
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
