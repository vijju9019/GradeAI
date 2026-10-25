import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  UploadCloud,
  CheckSquare,
  FileText,
  BarChart3,
  Settings,
  ShieldCheck,
  GraduationCap
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/examinations', label: 'Examinations', icon: BookOpen },
    { to: '/upload', label: 'Answer Upload', icon: UploadCloud },
    { to: '/review', label: 'Teacher Review', icon: CheckSquare },
    { to: '/reports', label: 'Results & Reports', icon: FileText },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 shrink-0">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center space-x-3 border-b border-slate-800 bg-slate-950/40">
        <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-600/30">
          <GraduationCap className="w-5 h-5" />
        </div>
        <div>
          <span className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
            GradeAI
            <span className="text-[10px] font-semibold uppercase bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-500/30">v1.0</span>
          </span>
          <p className="text-[11px] text-slate-400 font-medium">Exam Evaluation</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Academic Workspace
        </div>
        {navLinks.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20'
                    : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 mr-3 shrink-0 opacity-80" />
              {link.label}
            </NavLink>
          );
        })}
      </nav>

      {/* Human-in-the-Loop Seal */}
      <div className="p-4 mx-3 mb-4 rounded-xl bg-slate-800/50 border border-slate-800 text-xs">
        <div className="flex items-center space-x-2 text-indigo-400 font-semibold mb-1">
          <ShieldCheck className="w-4 h-4" />
          <span>Human-in-the-Loop</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          AI suggestions assist evaluation. All marks require verified teacher approval.
        </p>
      </div>

      {/* User Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center font-medium text-white text-xs shrink-0">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-medium text-white truncate">{user?.full_name}</p>
            <p className="text-[10px] text-slate-400 capitalize">{user?.role}</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
