'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SurfaceProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function Surface({
  children,
  title,
  subtitle,
  actions,
  className,
}: SurfaceProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'overflow-hidden rounded-[24px] border border-white/10 bg-slate-950/60 shadow-2xl shadow-black/20 backdrop-blur-xl',
        className
      )}
    >
      {title || subtitle || actions ? (
        <div className="flex flex-col gap-4 border-b border-white/10 px-5 py-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-1">
            {title ? <h2 className="text-lg font-semibold text-white">{title}</h2> : null}
            {subtitle ? <p className="text-sm text-slate-400">{subtitle}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
        </div>
      ) : null}
      <div className="p-5">{children}</div>
    </motion.section>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  helper?: string;
  tone?: 'default' | 'accent' | 'success' | 'warning';
}

export function StatCard({
  label,
  value,
  helper,
  tone = 'default',
}: StatCardProps) {
  const toneClasses = {
    default: 'from-white/8 to-white/4',
    accent: 'from-f1-red/20 to-orange-500/10',
    success: 'from-emerald-500/20 to-emerald-400/5',
    warning: 'from-amber-500/20 to-yellow-400/5',
  };

  return (
    <div
      className={cn(
        'rounded-[20px] border border-white/8 bg-gradient-to-br p-4',
        toneClasses[tone]
      )}
    >
      <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-slate-400">
        {label}
      </p>
      <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
      {helper ? <p className="mt-2 text-sm text-slate-400">{helper}</p> : null}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="rounded-[20px] border border-dashed border-white/10 bg-white/[0.03] px-5 py-10 text-center">
      <p className="text-lg font-medium text-white">{title}</p>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400">
        {description}
      </p>
      {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
    </div>
  );
}
