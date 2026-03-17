'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import { getDriverDisplayName } from '@/lib/driver';
import { cn } from '@/lib/utils';

interface SimpleDriver {
  driver_number: number;
  name_acronym: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  broadcast_name?: string;
  team_name: string;
  team_colour: string;
  country_code: string;
  headshot_url?: string;
}

interface SimpleDriverCardProps {
  driver: SimpleDriver;
  isSelected?: boolean;
  onToggle?: () => void;
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
  'RB': '#6692FF',
  'Kick Sauber': '#52E252',
};

export default function SimpleDriverCard({
  driver,
  isSelected = false,
  onToggle,
}: SimpleDriverCardProps) {
  const teamColor = teamColors[driver.team_name] || `#${driver.team_colour}` || '#666666';
  const driverName = getDriverDisplayName(driver);

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onToggle}
      className={cn(
        'relative overflow-hidden rounded-lg bg-gray-800/50 backdrop-blur-sm cursor-pointer transition-all',
        'border border-transparent hover:border-white/10',
        isSelected && 'ring-2 ring-f1-red border-f1-red'
      )}
      role="button"
      tabIndex={0}
      aria-label={`Driver ${driverName}`}
      onKeyDown={(e) => e.key === 'Enter' && onToggle?.()}
    >
      {/* Team color accent */}
      <div
        className="absolute left-0 top-0 h-full w-1"
        style={{ backgroundColor: teamColor }}
      />

      <div className="p-4 pl-4">
        <div className="flex items-center gap-4">
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
              {driverName}
            </p>
            <p className="text-xs text-gray-500">{driver.team_name}</p>
          </div>

          {/* Driver headshot */}
          {driver.headshot_url && (
            <div className="relative h-12 w-12 flex-shrink-0 overflow-hidden rounded-full bg-gray-700">
              <Image
                src={driver.headshot_url}
                alt={driverName}
                fill
                className="object-cover"
              />
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
