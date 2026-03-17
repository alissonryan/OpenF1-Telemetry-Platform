'use client';

import { motion } from 'framer-motion';
import { getDriverDisplayName } from '@/lib/driver';

interface Driver {
  driver_number: number;
  name_acronym: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  broadcast_name?: string;
  team_name: string;
  team_colour: string;
}

interface Position {
  position: number;
  date: string;
  driver_number: number;
}

interface IntervalData {
  driver_number: number;
  gap_to_leader?: number | null;
  interval?: number | null;
}

interface LeaderboardProps {
  positions: Position[];
  drivers: Driver[];
  intervals?: IntervalData[];
}

export default function Leaderboard({
  positions,
  drivers,
  intervals = [],
}: LeaderboardProps) {
  // Sort positions and get latest position for each driver
  const leaderboard = positions
    .sort((a, b) => a.position - b.position)
    .reduce((acc, pos) => {
      if (!acc.find((p) => p.driver_number === pos.driver_number)) {
        acc.push(pos);
      }
      return acc;
    }, [] as Position[])
    .slice(0, 20);

  const getDriver = (driverNumber: number) => {
    return drivers.find((d) => d.driver_number === driverNumber);
  };

  const getPositionColor = (position: number) => {
    if (position === 1) return 'text-yellow-400';
    if (position === 2) return 'text-gray-300';
    if (position === 3) return 'text-amber-600';
    return 'text-white';
  };

  const latestIntervals = intervals.reduce<Record<number, IntervalData>>((acc, item) => {
    acc[item.driver_number] = item;
    return acc;
  }, {});

  if (leaderboard.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg bg-gray-800/50 p-6 backdrop-blur">
      <h2 className="mb-4 text-xl font-semibold text-white">Leaderboard</h2>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700 text-left text-sm text-gray-400">
              <th className="pb-3 pr-4">Pos</th>
              <th className="pb-3 pr-4">Driver</th>
              <th className="pb-3 pr-4">Team</th>
              <th className="pb-3">Gap</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((pos, index) => {
              const driver = getDriver(pos.driver_number);
              if (!driver) return null;

              return (
                <motion.tr
                  key={pos.driver_number}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="border-b border-gray-700/50 text-sm"
                >
                  <td className={`py-3 pr-4 font-bold ${getPositionColor(pos.position)}`}>
                    {pos.position}
                  </td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-1 w-1 rounded-full"
                        style={{ backgroundColor: `#${driver.team_colour}` }}
                      />
                      <span className="font-semibold text-white">{driver.name_acronym}</span>
                      <span className="text-gray-400">{getDriverDisplayName(driver)}</span>
                    </div>
                  </td>
                  <td className="py-3 pr-4 text-gray-400">{driver.team_name}</td>
                  <td className="py-3 text-gray-400">
                    {pos.position === 1
                      ? 'LEADER'
                      : latestIntervals[pos.driver_number]?.gap_to_leader != null
                        ? `+${latestIntervals[pos.driver_number].gap_to_leader?.toFixed(3)}s`
                        : latestIntervals[pos.driver_number]?.interval != null
                          ? `+${latestIntervals[pos.driver_number].interval?.toFixed(3)}s`
                          : 'N/A'}
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
