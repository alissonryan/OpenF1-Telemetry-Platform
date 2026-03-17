'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import type { Driver } from '@/types';

interface DriverCardProps {
  driver: Driver;
  position?: number;
  lapTime?: string;
  gap?: string;
  isSelected?: boolean;
  onClick?: () => void;
  showDetails?: boolean;
}

const teamColors: Record<string, string> = {
  'Mercedes': '#00D2BE',
  'Red Bull Racing': '#0600EF',
  'Ferrari': '#DC0000',
  'McLaren': '#FF8700',
  'Aston Martin': '#006F62',
  'Alpine': '#0090FF',
  'Williams': '#005AFF',
  'AlphaTauri': '#2B4562',
  'Alfa Romeo': '#900000',
  'Haas F1 Team': '#FFFFFF',
};

export default function DriverCard({
  driver,
  position,
  lapTime,
  gap,
  isSelected = false,
  onClick,
  showDetails = true,
}: DriverCardProps) {
  const teamColor = teamColors[driver.team_name] || '#666666';

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-lg bg-gray-800/50 backdrop-blur-sm cursor-pointer transition-all',
        'border border-transparent hover:border-white/10',
        isSelected && 'ring-2 ring-f1-red border-f1-red'
      )}
      role="button"
      tabIndex={0}
      aria-label={`Driver ${driver.broadcast_name}, position ${position}`}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
    >
      {/* Team color accent */}
      <div
        className="absolute left-0 top-0 h-full w-1"
        style={{ backgroundColor: teamColor }}
      />

      <div className="p-4 pl-4">
        <div className="flex items-center gap-4">
          {/* Position */}
          {position !== undefined && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-white/5 text-xl font-bold text-white"
            >
              {position}
            </motion.div>
          )}

          {/* Driver number and name */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className="text-sm font-mono font-bold"
                style={{ color: teamColor }}
              >
                {driver.driver_number}
              </span>
              <span className="text-sm font-medium text-gray-400">
                {driver.name_acronym}
              </span>
            </div>
            <p className="truncate text-base font-semibold text-white">
              {driver.broadcast_name}
            </p>
            {showDetails && (
              <p className="text-xs text-gray-500">{driver.team_name}</p>
            )}
          </div>

          {/* Driver headshot */}
          {driver.headshot_url && (
            <div className="relative h-12 w-12 flex-shrink-0 overflow-hidden rounded-full bg-gray-700">
              <Image
                src={driver.headshot_url}
                alt={driver.broadcast_name}
                fill
                className="object-cover"
              />
            </div>
          )}

          {/* Timing info */}
          {(lapTime || gap) && (
            <div className="flex flex-col items-end">
              {lapTime && (
                <span className="font-mono text-sm font-semibold text-white">
                  {lapTime}
                </span>
              )}
              {gap && (
                <span className="font-mono text-xs text-gray-400">
                  {gap}
                </span>
              )}
            </div>
          )}

          {/* Country flag */}
          <div className="flex h-6 w-8 flex-shrink-0 items-center justify-center rounded bg-white/10 text-xs font-bold text-white">
            {driver.country_code}
          </div>
        </div>
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute right-2 top-2 h-2 w-2 rounded-full bg-f1-red"
        />
      )}
    </motion.div>
  );
}

// Skeleton loader for DriverCard
export function DriverCardSkeleton() {
  return (
    <div className="animate-pulse rounded-lg bg-gray-800/50 p-4">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-lg bg-gray-700" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-16 rounded bg-gray-700" />
          <div className="h-4 w-32 rounded bg-gray-700" />
        </div>
        <div className="h-12 w-12 rounded-full bg-gray-700" />
      </div>
    </div>
  );
}
