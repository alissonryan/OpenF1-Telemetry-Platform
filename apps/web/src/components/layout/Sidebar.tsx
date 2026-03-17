'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { primaryNavigation, secondaryNavigation } from '@/lib/navigation';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

const iconByHref: Record<string, React.ReactNode> = {
  '/dashboard': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  ),
  '/telemetry': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 13h4l2-6 4 12 2-6h4" />
    </svg>
  ),
  '/predictions': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  '/drivers': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
  '/circuits': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
    </svg>
  ),
  '/historical': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  '/settings': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  '/help': (
    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

export default function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const pathname = usePathname();

  const MenuItem = ({ href, label, icon }: { href: string; label: string; icon: React.ReactNode }) => {
    const isActive = pathname.startsWith(href);
    
    return (
      <Link href={href} className="block">
        <motion.div
          whileHover={{ x: 4 }}
          whileTap={{ scale: 0.98 }}
          className={cn(
            'flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors',
            isActive
              ? 'bg-f1-red/20 text-f1-red'
              : 'text-gray-400 hover:bg-white/5 hover:text-white'
          )}
        >
          <span className="flex-shrink-0">{icon}</span>
          {isOpen && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="text-sm font-medium whitespace-nowrap overflow-hidden"
            >
              {label}
            </motion.span>
          )}
          {isActive && (
            <motion.div
              layoutId="activeIndicator"
              className="absolute left-0 w-1 h-8 bg-f1-red rounded-r-full"
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            />
          )}
        </motion.div>
      </Link>
    );
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2"
          >
            <div className="h-8 w-8 rounded-lg bg-f1-red flex items-center justify-center">
              <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <span className="font-bold text-white">F1 Telemetry</span>
          </motion.div>
        )}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white"
          aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <svg
            className={cn('h-5 w-5 transition-transform', !isOpen && 'rotate-180')}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </motion.button>
      </div>

      <nav className="flex-1 overflow-y-auto p-3">
        <div className="space-y-1">
          {primaryNavigation.map((item) => (
            <MenuItem
              key={item.href}
              href={item.href}
              label={item.label}
              icon={iconByHref[item.href]}
            />
          ))}
        </div>

        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 pt-6 border-t border-white/10"
          >
            <p className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Support
            </p>
          </motion.div>
        )}

        <div className="mt-2 space-y-1">
          {secondaryNavigation.map((item) => (
            <MenuItem
              key={item.href}
              href={item.href}
              label={item.label}
              icon={iconByHref[item.href]}
            />
          ))}
        </div>
      </nav>

      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 border-t border-white/10"
        >
          <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-f1-red/15 via-white/5 to-white/[0.02] p-4">
            <p className="text-sm font-medium text-white">Data Stack</p>
            <p className="mt-1 text-xs leading-5 text-gray-400">
              OpenF1 for live timing, FastF1 for historical analysis, F1DB for long-range records and Open-Meteo for circuit weather.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {['OpenF1', 'FastF1', 'F1DB', 'Open-Meteo'].map((label) => (
                <span
                  key={label}
                  className="rounded-full border border-white/10 bg-black/20 px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.2em] text-gray-300"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
