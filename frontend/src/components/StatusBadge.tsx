import React from 'react';
import { AlertTriangle, CheckCircle2, Clock, FileCheck, HelpCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const norm = (status || '').toLowerCase().replace(/_/g, ' ');

  let bg = 'bg-slate-100 text-slate-700 border-slate-200';
  let icon = <Clock className="w-3.5 h-3.5 mr-1" />;

  if (norm.includes('finalized') || norm === 'approved') {
    bg = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    icon = <FileCheck className="w-3.5 h-3.5 mr-1" />;
  } else if (norm.includes('reviewed') || norm.includes('evaluated')) {
    bg = 'bg-blue-50 text-blue-700 border-blue-200';
    icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1" />;
  } else if (norm.includes('pending') || norm.includes('processing')) {
    bg = 'bg-amber-50 text-amber-700 border-amber-200';
    icon = <Clock className="w-3.5 h-3.5 mr-1" />;
  } else if (norm.includes('high')) {
    bg = 'bg-teal-50 text-teal-700 border-teal-200';
    icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1" />;
  } else if (norm.includes('low')) {
    bg = 'bg-rose-50 text-rose-700 border-rose-200';
    icon = <AlertTriangle className="w-3.5 h-3.5 mr-1" />;
  } else if (norm.includes('medium')) {
    bg = 'bg-amber-50 text-amber-700 border-amber-200';
    icon = <HelpCircle className="w-3.5 h-3.5 mr-1" />;
  } else if (norm.includes('ready')) {
    bg = 'bg-indigo-50 text-indigo-700 border-indigo-200';
    icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1" />;
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center rounded-full border ${padding} ${bg} capitalize tracking-wide`}>
      {icon}
      {norm}
    </span>
  );
};
