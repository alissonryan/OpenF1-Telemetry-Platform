'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ConnectionState } from '@/hooks/useWebSocket';

interface ConnectionStatusProps {
  isConnected: boolean;
  connectionState?: ConnectionState;
  lastHeartbeat?: number | null;
  showDetails?: boolean;
  className?: string;
}

export default function ConnectionStatus({
  isConnected,
  connectionState = 'disconnected',
  lastHeartbeat,
  showDetails = false,
  className = '',
}: ConnectionStatusProps) {
  const getStatusConfig = () => {
    switch (connectionState) {
      case 'connected':
        return {
          color: 'bg-green-500',
          textColor: 'text-green-500',
          label: 'LIVE',
          icon: '●',
          pulse: true,
        };
      case 'connecting':
        return {
          color: 'bg-yellow-500',
          textColor: 'text-yellow-500',
          label: 'CONNECTING',
          icon: '◐',
          pulse: true,
        };
      case 'error':
        return {
          color: 'bg-red-500',
          textColor: 'text-red-500',
          label: 'ERROR',
          icon: '✕',
          pulse: false,
        };
      case 'disconnected':
      default:
        return {
          color: 'bg-gray-500',
          textColor: 'text-gray-500',
          label: 'OFFLINE',
          icon: '○',
          pulse: false,
        };
    }
  };

  const config = getStatusConfig();

  // Calculate time since last heartbeat
  const getTimeSinceHeartbeat = () => {
    if (!lastHeartbeat) return null;
    const seconds = Math.floor((Date.now() - lastHeartbeat) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ago`;
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Status Indicator */}
      <div className="flex items-center gap-2">
        <div className="relative">
          {/* Pulse animation for live connection */}
          <AnimatePresence>
            {config.pulse && isConnected && (
              <motion.div
                initial={{ scale: 1, opacity: 0.5 }}
                animate={{ scale: 2, opacity: 0 }}
                exit={{ scale: 1, opacity: 0 }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className={`absolute inset-0 rounded-full ${config.color}`}
              />
            )}
          </AnimatePresence>
          
          {/* Status dot */}
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className={`relative h-3 w-3 rounded-full ${config.color}`}
          />
        </div>

        {/* Status Label */}
        <motion.span
          key={config.label}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className={`font-mono text-sm font-bold ${config.textColor}`}
        >
          {config.label}
        </motion.span>
      </div>

      {/* Details (optional) */}
      {showDetails && (
        <div className="flex items-center gap-2 text-xs text-gray-400">
          {isConnected && lastHeartbeat && (
            <span className="flex items-center gap-1">
              <svg
                className="h-3 w-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              {getTimeSinceHeartbeat()}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// Compact version for inline use
export function ConnectionBadge({
  isConnected,
  className = '',
}: {
  isConnected: boolean;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
        isConnected
          ? 'bg-green-500/20 text-green-400'
          : 'bg-gray-500/20 text-gray-400'
      } ${className}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          isConnected ? 'bg-green-500' : 'bg-gray-500'
        }`}
      />
      {isConnected ? 'LIVE' : 'OFFLINE'}
    </span>
  );
}

// Animated F1-style connection indicator
export function F1ConnectionIndicator({
  isConnected,
  connectionState,
}: {
  isConnected: boolean;
  connectionState?: ConnectionState;
}) {
  return (
    <motion.div
      className="flex items-center gap-2 rounded-lg bg-black/50 px-3 py-1.5"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* F1-style animated stripes */}
      <div className="flex gap-0.5">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className={`h-4 w-1 rounded-sm ${
              isConnected ? 'bg-f1-red' : 'bg-gray-600'
            }`}
            animate={
              isConnected
                ? {
                    scaleY: [1, 1.5, 1],
                    opacity: [0.5, 1, 0.5],
                  }
                : {}
            }
            transition={{
              duration: 0.8,
              repeat: Infinity,
              delay: i * 0.2,
            }}
          />
        ))}
      </div>

      {/* Status text */}
      <span
        className={`font-mono text-sm font-bold tracking-wider ${
          isConnected ? 'text-white' : 'text-gray-500'
        }`}
      >
        {isConnected ? 'LIVE' : 'OFFLINE'}
      </span>

      {/* Connection state indicator */}
      {connectionState === 'connecting' && (
        <motion.span
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1, repeat: Infinity }}
          className="text-xs text-yellow-500"
        >
          Connecting...
        </motion.span>
      )}
    </motion.div>
  );
}
