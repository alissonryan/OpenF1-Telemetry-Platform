'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: React.ReactNode;
  className?: string;
}

export default function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative overflow-hidden rounded-[28px] border border-white/10 bg-white/5 p-6 backdrop-blur-xl',
        className
      )}
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />
      <div className="absolute right-0 top-0 h-36 w-36 rounded-full bg-f1-red/15 blur-3xl" />
      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl space-y-3">
          {eyebrow ? (
            <p className="font-mono text-xs uppercase tracking-[0.32em] text-red-200/80">
              {eyebrow}
            </p>
          ) : null}
          <div className="space-y-2">
            <h1 className="font-display text-4xl font-semibold uppercase tracking-[0.04em] text-white sm:text-5xl">
              {title}
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">
              {description}
            </p>
          </div>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </div>
    </motion.div>
  );
}
