'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState, useCallback } from 'react';
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

const mainVariants = {
  open: { marginLeft: 280 },
  closed: { marginLeft: 80 },
};

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  return (
    <div className="flex min-h-screen bg-f1-dark">
      <motion.aside
        initial="open"
        animate={sidebarOpen ? 'open' : 'closed'}
        variants={sidebarVariants}
        className="fixed left-0 top-0 z-40 h-screen border-r border-white/10 bg-gray-900/95 backdrop-blur-lg"
      >
        <Sidebar isOpen={sidebarOpen} onToggle={toggleSidebar} />
      </motion.aside>

      <div className="flex flex-1 flex-col">
        <Header onMenuClick={toggleSidebar} />

        <motion.main
          initial="open"
          animate={sidebarOpen ? 'open' : 'closed'}
          variants={mainVariants}
          className="flex-1 overflow-auto p-6"
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
