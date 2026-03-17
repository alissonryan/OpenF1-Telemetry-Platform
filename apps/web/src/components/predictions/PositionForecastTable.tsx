'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface PositionForecast {
  driver_number: number;
  driver_name?: string;
  team_name?: string;
  current_position: number;
  predicted_position: number;
  position_change: number;
  confidence: number;
  factors?: string[];
}

interface PositionForecastTableProps {
  predictions: PositionForecast[];
  isLoading?: boolean;
}

const teamColors: Record<string, string> = {
  'Mercedes': '#00D2BE',
  'Red Bull Racing': '#0600EF',
  'Ferrari': '#DC0000',
  'McLaren': '#FF8700',
  'Aston Martin': '#006F62',
  'Alpine': '#0090FF',
  'Williams': '#005AFF',
  'RB': '#6692FF',
  'Kick Sauber': '#52E252',
  'Haas F1 Team': '#FFFFFF',
};

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'text-green-400';
  if (confidence >= 0.5) return 'text-yellow-400';
  return 'text-red-400';
}

function getPositionChangeIndicator(change: number) {
  if (change > 0) {
    return (
      <span className="flex items-center gap-0.5 text-green-400">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
        +{change}
      </span>
    );
  } else if (change < 0) {
    return (
      <span className="flex items-center gap-0.5 text-red-400">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
        {change}
      </span>
    );
  }
  return <span className="text-gray-400">-</span>;
}

export default function PositionForecastTable({ predictions, isLoading }: PositionForecastTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl bg-gray-800/50 backdrop-blur-sm border border-white/10 p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-700 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-gray-800/50 backdrop-blur-sm border border-white/10 overflow-hidden"
    >
      {/* Header */}
      <div className="bg-gray-900/50 px-4 py-3 border-b border-white/10">
        <h3 className="text-lg font-semibold text-white">Position Forecast</h3>
        <p className="text-xs text-gray-400 mt-1">Predicted finishing positions</p>
      </div>
      
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs text-gray-400 border-b border-white/5">
              <th className="px-4 py-3 font-medium">Pos</th>
              <th className="px-4 py-3 font-medium">Driver</th>
              <th className="px-4 py-3 font-medium text-center">Current</th>
              <th className="px-4 py-3 font-medium text-center">Predicted</th>
              <th className="px-4 py-3 font-medium text-center">Change</th>
              <th className="px-4 py-3 font-medium text-center">Confidence</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence>
              {predictions.map((pred, index) => {
                const teamColor = teamColors[pred.team_name || ''] || '#666666';
                
                return (
                  <motion.tr
                    key={pred.driver_number}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.03 }}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="text-sm font-mono text-gray-300">
                        P{index + 1}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-1 h-8 rounded-full"
                          style={{ backgroundColor: teamColor }}
                        />
                        <div>
                          <p className="font-medium text-white">{pred.driver_name || `Driver ${pred.driver_number}`}</p>
                          <p className="text-xs text-gray-500">{pred.team_name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-lg font-semibold text-white">
                        {pred.current_position}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-lg font-semibold text-f1-red">
                        {pred.predicted_position}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getPositionChangeIndicator(pred.position_change)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <motion.div
                            className={cn('h-full rounded-full', 
                              pred.confidence >= 0.8 ? 'bg-green-500' :
                              pred.confidence >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                            )}
                            initial={{ width: 0 }}
                            animate={{ width: `${pred.confidence * 100}%` }}
                            transition={{ duration: 0.5, delay: index * 0.03 }}
                          />
                        </div>
                        <span className={cn('text-xs font-medium', getConfidenceColor(pred.confidence))}>
                          {(pred.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
      
      {/* Legend */}
      <div className="px-4 py-3 bg-gray-900/30 border-t border-white/5">
        <div className="flex items-center gap-6 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>High confidence (≥80%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span>Medium (50-79%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>Low (&lt;50%)</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
