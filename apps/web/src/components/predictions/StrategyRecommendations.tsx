'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { StrategyAnalysis } from '@/types/predictions';

interface StrategyRecommendationsProps {
  recommendations: StrategyAnalysis[];
  isLoading?: boolean;
}

const compoundColors: Record<string, string> = {
  'SOFT': 'bg-red-500 text-white',
  'MEDIUM': 'bg-yellow-500 text-black',
  'HARD': 'bg-white text-black',
  'INTERMEDIATE': 'bg-blue-500 text-white',
  'WET': 'bg-blue-700 text-white',
};

const riskColors: Record<string, { bg: string; text: string }> = {
  'low': { bg: 'bg-green-500/20', text: 'text-green-400' },
  'medium': { bg: 'bg-yellow-500/20', text: 'text-yellow-400' },
  'high': { bg: 'bg-red-500/20', text: 'text-red-400' },
};

export default function StrategyRecommendations({ 
  recommendations, 
  isLoading 
}: StrategyRecommendationsProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl bg-gray-800/50 backdrop-blur-sm border border-white/10 p-6">
        <div className="animate-pulse space-y-6">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-700 rounded-lg" />
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
      <div className="bg-gray-900/50 px-6 py-4 border-b border-white/10">
        <h2 className="text-lg font-semibold text-white">Strategy Recommendations</h2>
        <p className="text-sm text-gray-400 mt-1">Optimal pit stop windows and compound strategies</p>
      </div>
      
      {/* Recommendations Grid */}
      <div className="p-4 space-y-4">
        {recommendations.map((rec, index) => (
          <StrategyCard key={rec.driver_number} strategy={rec} index={index} />
        ))}
      </div>
      
      {/* Legend */}
      <div className="px-6 py-3 bg-gray-900/30 border-t border-white/5">
        <div className="flex items-center gap-6 text-xs text-gray-400">
          <span className="font-medium">Compounds:</span>
          <div className="flex items-center gap-2">
            <span className={cn('px-2 py-0.5 rounded text-xs font-medium', compoundColors['SOFT'])}>S</span>
            <span>Soft</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={cn('px-2 py-0.5 rounded text-xs font-medium', compoundColors['MEDIUM'])}>M</span>
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={cn('px-2 py-0.5 rounded text-xs font-medium', compoundColors['HARD'])}>H</span>
            <span>Hard</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function StrategyCard({ strategy, index }: { strategy: StrategyAnalysis; index: number }) {
  const riskStyle = riskColors[strategy.risk_level] || riskColors['medium'];
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-gray-900/50 rounded-lg p-4 border border-white/5"
    >
      {/* Header Row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-white">#{strategy.driver_number}</span>
          <span className={cn(
            'px-2 py-0.5 rounded text-xs font-medium',
            compoundColors[strategy.current_compound] || 'bg-gray-500'
          )}>
            {strategy.current_compound}
          </span>
          <span className="text-xs text-gray-400">
            {strategy.tyre_age} laps old
          </span>
        </div>
        
        <div className="flex items-center gap-3">
          <span className={cn('px-2 py-1 rounded text-xs font-medium', riskStyle.bg, riskStyle.text)}>
            {strategy.risk_level.toUpperCase()} RISK
          </span>
        </div>
      </div>
      
      {/* Timeline */}
      {strategy.optimal_laps.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-400 mb-2">Recommended Pit Windows:</p>
          <div className="relative">
            {/* Timeline bar */}
            <div className="h-8 bg-gray-700/50 rounded-lg relative overflow-hidden">
              {/* Lap markers */}
              <div className="absolute inset-0 flex justify-between px-2 items-center text-xs text-gray-500">
                <span>L1</span>
                <span>L25</span>
                <span>L50</span>
              </div>
              
              {/* Pit stop markers */}
              {strategy.optimal_laps.map((lap, i) => {
                const position = (lap / 50) * 100;
                return (
                  <motion.div
                    key={i}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 + i * 0.1 }}
                    className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-f1-red rounded-full border-2 border-white shadow-lg cursor-pointer hover:scale-110 transition-transform"
                    style={{ left: `${position}%`, transform: 'translateX(-50%) translateY(-50%)' }}
                    title={`Pit lap ${lap} - ${strategy.compounds[i] || 'Unknown'}`}
                  >
                    <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-xs text-white whitespace-nowrap">
                      L{lap}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>
      )}
      
      {/* Strategy Details */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-xs text-gray-400">Stops</p>
          <p className="text-xl font-bold text-white">{strategy.recommended_stops}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Expected Gain</p>
          <p className={cn(
            'text-xl font-bold',
            strategy.expected_positions_gained > 0 ? 'text-green-400' : 
            strategy.expected_positions_gained < 0 ? 'text-red-400' : 'text-gray-400'
          )}>
            {strategy.expected_positions_gained > 0 ? '+' : ''}{strategy.expected_positions_gained.toFixed(1)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Confidence</p>
          <p className="text-xl font-bold text-white">{(strategy.confidence * 100).toFixed(0)}%</p>
        </div>
      </div>
      
      {/* Compounds recommendation */}
      {strategy.compounds.length > 0 && (
        <div className="mt-4 pt-4 border-t border-white/5">
          <p className="text-xs text-gray-400 mb-2">Recommended Compounds:</p>
          <div className="flex gap-2">
            {strategy.compounds.map((compound, i) => (
              <span key={i} className={cn(
                'px-3 py-1 rounded text-sm font-medium',
                compoundColors[compound] || 'bg-gray-500'
              )}>
                {compound}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Factors */}
      {strategy.factors.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-400 mb-1">Key Factors:</p>
          <div className="flex flex-wrap gap-1">
            {strategy.factors.map((factor, i) => (
              <span key={i} className="text-xs text-gray-300 bg-gray-700/50 px-2 py-0.5 rounded">
                {factor}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Alternatives */}
      {strategy.alternative_strategies.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <p className="text-xs text-gray-400 mb-2">Alternative Strategies:</p>
          <div className="space-y-1">
            {strategy.alternative_strategies.map((alt, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <span className="text-gray-300">{alt.strategy}</span>
                <div className="flex items-center gap-2">
                  {alt.expected_gain !== undefined && (
                    <span className={cn(
                      alt.expected_gain > 0 ? 'text-green-400' : 
                      alt.expected_gain < 0 ? 'text-red-400' : 'text-gray-400'
                    )}>
                      {alt.expected_gain > 0 ? '+' : ''}{alt.expected_gain.toFixed(1)}
                    </span>
                  )}
                  <span className={cn(
                    'px-1.5 py-0.5 rounded text-xs',
                    riskColors[alt.risk]?.bg,
                    riskColors[alt.risk]?.text
                  )}>
                    {alt.risk}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
