import { Upload, FileText, Clock, AlertTriangle, Settings, ChevronLeft, ChevronRight, X, LogOut, Scale } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useDocuments } from '@/lib/documents';
import { useAuth } from '@/lib/auth';

interface AppSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onClose: () => void;
}

export function AppSidebar({ collapsed, onToggle, onClose }: AppSidebarProps) {
  const { documents } = useDocuments();
  const { user, logout } = useAuth();
  const processingCount = documents.filter(
    d => d.status === 'uploaded' || d.status === 'indexed' || d.status === 'analyzing'
  ).length;
  const failedCount = documents.filter(d => d.status === 'failed').length;

  const navItems = [
    { to: '/', icon: Upload, label: 'Upload', end: true, badge: 0 },
    { to: '/documents', icon: FileText, label: 'Documents', end: false, badge: 0 },
    { to: '/processing', icon: Clock, label: 'Processing', end: false, badge: processingCount },
    { to: '/failed', icon: AlertTriangle, label: 'Failed', end: false, badge: failedCount },
    { to: '/settings', icon: Settings, label: 'Settings', end: false, badge: 0 },
  ];

  return (
    <div className="h-full flex flex-col bg-sidebar">
      {/* Header */}
      <div className="h-14 flex items-center px-4 border-b border-sidebar-border shrink-0">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center">
              <Scale className="h-3.5 w-3.5 text-primary" />
            </div>
            <span className="font-semibold text-sm text-foreground tracking-tight">LegalMind</span>
          </div>
        )}
        {collapsed && (
          <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center mx-auto">
            <Scale className="h-3.5 w-3.5 text-primary" />
          </div>
        )}
        <button onClick={onClose} className="ml-auto p-1 rounded hover:bg-sidebar-accent lg:hidden transition-colors">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150',
                collapsed && 'justify-center px-0',
                isActive
                  ? 'bg-sidebar-accent text-foreground font-medium'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground'
              )
            }
          >
            <item.icon className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span>{item.label}</span>}
            {!collapsed && item.badge > 0 && (
              <span className="ml-auto text-[10px] font-semibold bg-primary/15 text-primary rounded-full px-2 py-0.5 min-w-[20px] text-center">
                {item.badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User + Collapse */}
      <div className="border-t border-sidebar-border shrink-0">
        {user && (
          <div className={cn('p-3', collapsed && 'flex justify-center')}>
            {!collapsed ? (
              <div className="flex items-center gap-3 px-3 py-2">
                <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center text-xs font-semibold text-primary shrink-0">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground truncate">{user.name}</p>
                  <p className="text-[11px] text-muted-foreground truncate">{user.email}</p>
                </div>
                <button onClick={logout} className="p-1.5 rounded-md hover:bg-sidebar-accent text-muted-foreground hover:text-foreground transition-colors" title="Sign out">
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <button onClick={logout} className="p-2 rounded-md hover:bg-sidebar-accent text-muted-foreground hover:text-foreground transition-colors" title="Sign out">
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
        <div className="p-3 pt-0 hidden lg:block">
          <button
            onClick={onToggle}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground w-full transition-colors',
              collapsed && 'justify-center px-0'
            )}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <><ChevronLeft className="h-4 w-4" /><span>Collapse</span></>}
          </button>
        </div>
      </div>
    </div>
  );
}
