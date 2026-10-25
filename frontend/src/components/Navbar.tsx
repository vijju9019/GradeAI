import React from 'react';
import { LogOut, Bell, User as UserIcon, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  title?: string;
  subtitle?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title = 'Overview', subtitle }) => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between shrink-0 sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-bold text-slate-800 leading-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {/* Role Indicator Badge */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
          <Shield className="w-3.5 h-3.5 text-indigo-600" />
          <span className="capitalize">{user?.role} Portal</span>
        </div>

        <div className="h-4 w-px bg-slate-200" />

        {/* User Info & Logout */}
        <div className="flex items-center space-x-3">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-semibold text-slate-800">{user?.full_name}</p>
            <p className="text-[11px] text-slate-400">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="flex items-center text-xs font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 px-2.5 py-1.5 rounded-lg border border-slate-200 transition-colors"
            title="Sign out of GradeAI"
          >
            <LogOut className="w-3.5 h-3.5 mr-1.5" />
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
};
