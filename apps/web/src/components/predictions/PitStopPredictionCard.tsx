'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { PitPrediction } from '@/types/predictions';

interface PitStopPredictionCardProps {
  driver: {
    driver_number: number;
    name_acronym: string;
    team_name: string;
    team_colour: string;
  };
  prediction: PitPrediction;
  isHighlighted?: boolean;
}

export default function PitStopPredictionCard({
  driver,
  prediction,
  isHighlighted = false,
}: PitStopPredictionCardProps) {
  const probability = prediction.probability * 100;
  const confidence = prediction.confidence * 100;
  
  // Determine color based on probability
  const getProbabilityColor = (prob: number) => {
    if (prob >= 70) return 'text-red-500';
    if (prob >= 40) return 'text-yellow-500';
    return 'text-green-500';
  };
  
  const getConfidenceColor = (conf: number) => {
    if (conf >= 80) return 'text-green-500';
    if (conf >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };
  
  // SVG circle progress
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (probability / 100) * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative overflow-hidden rounded-xl bg-gray-800/60 backdrop-blur-sm p-4',
        'border border-gray-700/50',
        isHighlighted && probability >= 70 && 'ring-2 ring-red-500/50 border-red-500/30'
      )}
    >
      {/* High probability alert */}
      {probability >= 70 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute top-2 right-2"
        >
          <span className="flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
          </span>
        </motion.div>
      )}
      
      <div className="flex items-start gap-4">
        {/* Driver info */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span
              className="text-sm font-mono font-bold"
              style={{ color: `#${driver.team_colour}` }}
            >
              {driver.driver_number}
            </span>
            <span className="text-sm font-medium text-gray-400">
              {driver.name_acronym}
            </span>
          </div>
          <p className="text-xs text-gray-500">{driver.team_name}</p>
        </div>
        
        {/* Probability circle */}
        <div className="relative w-24 h-24 flex-shrink-0">
          <svg className="w-24 h-24 transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="48"
              cy="48"
              r={radius}
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-gray-700"
            />
            {/* Progress circle */}
            <motion.circle
              cx="48"
              cy="48"
              r={radius}
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              className={getProbabilityColor(probability)}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={cn('text-2xl font-bold', getProbabilityColor(probability))}>
              {probability.toFixed(0)}%
            </span>
            <span className="text-xs text-gray-400">Pit Prob</span>
          </div>
        </div>
      </div>
      
      {/* Prediction details */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="bg-gray-900/50 rounded-lg p-2">
          <p className="text-xs text-gray-400 mb-1">Predicted Lap</p>
          <p className="text-lg font-semibold text-white">Lap {prediction.predicted_lap}</p>
        </div>
        
        <div className="bg-gray-900/50 rounded-lg p-2">
          <p className="text-xs text-gray-400 mb-1">Confidence</p>
          <p className={cn('text-lg font-semibold', getConfidenceColor(confidence))}>
            {confidence.toFixed(0)}%
          </p>
        </div>
      </div>
      
      {/* Recommended compound */}
      {prediction.recommended_compound && (
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs text-gray-400">Recommended:</span>
          <span className={cn(
            'px-2 py-0.5 rounded text-xs font-medium',
            prediction.recommended_compound === 'SOFT' && 'bg-red-500/20 text-red-400',
            prediction.recommended_compound === 'MEDIUM' && 'bg-yellow-500/20 text-yellow-400',
            prediction.recommended_compound === 'HARD' && 'bg-white/20 text-white',
          )}>
            {prediction.recommended_compound}
          </span>
        </div>
      )}
      
      {/* Reasons */}
      {prediction.reasons.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-gray-400 mb-1">Factors:</p>
          <ul className="space-y-1">
            {prediction.reasons.slice(0, 3).map((reason, idx) => (
              <li key={idx} className="text-xs text-gray-300 flex items-start gap-1">
                <span className="text-gray-500 mt-0.5">•</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}
