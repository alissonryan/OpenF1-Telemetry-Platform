'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';
import Header from './Header';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
}

const sidebarVariants = {
  open: {
    width: 280,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
  closed: {
    width: 80,
    transition: { type: 'spring', stiffness: 300, damping: 30 },
  },
};

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(min-width: 1024px)');
    const updateViewport = () => setIsDesktop(mediaQuery.matches);

    updateViewport();
    mediaQuery.addEventListener('change', updateViewport);
    return () => mediaQuery.removeEventListener('change', updateViewport);
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  return (
    <div className="min-h-screen bg-f1-dark">
      <AnimatePresence>
        {!isDesktop && sidebarOpen ? (
          <motion.button
            key="sidebar-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={toggleSidebar}
            className="fixed inset-0 z-30 bg-slate-950/70 backdrop-blur-sm lg:hidden"
            aria-label="Close navigation"
          />
        ) : null}
      </AnimatePresence>

      <motion.aside
        initial={false}
        animate={
          isDesktop
            ? sidebarOpen
              ? 'open'
              : 'closed'
            : sidebarOpen
              ? { x: 0, width: 320 }
              : { x: -340, width: 320 }
        }
        variants={isDesktop ? sidebarVariants : undefined}
        className={cn(
          'fixed left-0 top-0 z-40 h-screen border-r border-white/10 bg-gray-900/95 backdrop-blur-lg',
          !isDesktop && 'w-80'
        )}
      >
        <Sidebar isOpen={isDesktop ? sidebarOpen : true} onToggle={toggleSidebar} />
      </motion.aside>

      <div
        className={cn(
          'flex min-h-screen flex-1 flex-col transition-[padding-left] duration-300',
          isDesktop && (sidebarOpen ? 'lg:pl-[280px]' : 'lg:pl-20')
        )}
      >
        <Header onMenuClick={toggleSidebar} />

        <motion.main
          className="flex-1 overflow-auto px-4 py-5 sm:px-6"
        >
          <AnimatePresence mode="wait">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="h-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </motion.main>
      </div>
    </div>
  );
}
