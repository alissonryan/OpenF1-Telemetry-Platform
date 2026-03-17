'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-white/10 bg-gray-900/80 px-6 backdrop-blur-lg">
      <div className="flex items-center gap-4">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onMenuClick}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/5 text-white transition-colors hover:bg-white/10"
          aria-label="Toggle sidebar"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </motion.button>

        <Link href="/" className="flex items-center gap-3">
          <motion.div
            whileHover={{ rotate: 5 }}
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-f1-red"
          >
            <svg
              className="h-6 w-6 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </motion.div>
          <span className="text-xl font-bold text-white">F1 Telemetry</span>
        </Link>
      </div>


      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 md:flex">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="font-mono text-[11px] uppercase tracking-[0.24em] text-slate-300">
            Live + Historical
          </span>
        </div>
        <Link
          href="/help"
          className="hidden rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-300 transition-colors hover:border-white/20 hover:text-white md:inline-flex"
        >
          Data Sources
        </Link>
        <Link href="/settings">
          <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/5 text-white transition-colors hover:bg-white/10"
          aria-label="Settings"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          </motion.div>
        </Link>
      </div>
    </header>
  );
}
