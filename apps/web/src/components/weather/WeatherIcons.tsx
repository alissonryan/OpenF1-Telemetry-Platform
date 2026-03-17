'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface WeatherIconProps {
  code: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  isNight?: boolean;
}

const sizeClasses = {
  sm: 'w-6 h-6',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
};

// Weather icons as inline SVGs
export function WeatherIcon({ code, size = 'md', className, isNight = false }: WeatherIconProps) {
  const iconType = getWeatherIconType(code);
  const IconComponent = getIconComponent(iconType, isNight);
  
  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={cn(sizeClasses[size], className)}
    >
      {IconComponent}
    </motion.div>
  );
}

function getWeatherIconType(code: number): string {
  if (code === 0) return 'clear';
  if (code >= 1 && code <= 3) return 'partly-cloudy';
  if (code === 45 || code === 48) return 'fog';
  if (code >= 51 && code <= 57) return 'drizzle';
  if (code >= 61 && code <= 67) return 'rain';
  if (code >= 71 && code <= 77) return 'snow';
  if (code >= 80 && code <= 82) return code === 82 ? 'heavy-rain' : 'rain';
  if (code >= 85 && code <= 86) return 'heavy-snow';
  if (code >= 95 && code <= 99) return 'thunderstorm';
  return 'unknown';
}

function getIconComponent(type: string, isNight: boolean): React.ReactNode {
  const icons: Record<string, React.ReactNode> = {
    clear: isNight ? <MoonIcon /> : <SunIcon />,
    'partly-cloudy': isNight ? <MoonCloudIcon /> : <SunCloudIcon />,
    cloudy: <CloudIcon />,
    fog: <FogIcon />,
    drizzle: <DrizzleIcon />,
    rain: <RainIcon />,
    'heavy-rain': <HeavyRainIcon />,
    snow: <SnowIcon />,
    'heavy-snow': <HeavySnowIcon />,
    thunderstorm: <ThunderstormIcon />,
    unknown: <UnknownIcon />,
  };
  
  return icons[type] ?? <UnknownIcon />;
}

// Icon components
function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="4" className="fill-yellow-400" />
      <motion.g
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
      >
        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => (
          <line
            key={angle}
            x1="12"
            y1="2"
            x2="12"
            y2="4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            className="stroke-yellow-400"
            transform={`rotate(${angle} 12 12)`}
          />
        ))}
      </motion.g>
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
        className="fill-slate-300"
      />
      <circle cx="14" cy="8" r="1" className="fill-slate-400" />
      <circle cx="17" cy="12" r="0.5" className="fill-slate-400" />
    </svg>
  );
}

function SunCloudIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="8" cy="8" r="3" className="fill-yellow-400" />
      <motion.g
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        style={{ transformOrigin: '8px 8px' }}
      >
        {[0, 90, 180, 270].map((angle) => (
          <line
            key={angle}
            x1="8"
            y1="3"
            x2="8"
            y2="4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            className="stroke-yellow-400"
            transform={`rotate(${angle} 8 8)`}
          />
        ))}
      </motion.g>
      <path
        d="M20 17a3 3 0 100-6h-.5a5 5 0 00-9.5 0 4 4 0 000 8h10a3 3 0 000-2z"
        className="fill-slate-400"
      />
    </svg>
  );
}

function MoonCloudIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M9 5a5 5 0 014.5 2.5 4 4 0 00-1.5 7.5h6a3 3 0 100-6h-.5A5 5 0 109 5z"
        className="fill-slate-400"
      />
      <path
        d="M7 6a2 2 0 011.5.5 3 3 0 00-2 2.5 1 1 0 00.5 1 2 2 0 01-1.5-1 2 2 0 011.5-3z"
        className="fill-slate-300"
      />
    </svg>
  );
}

function CloudIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M20 17a3 3 0 100-6h-.5a5 5 0 00-9.5 0 4 4 0 000 8h10a3 3 0 000-2z"
        className="fill-slate-400"
      />
    </svg>
  );
}

function FogIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <motion.line
        x1="4"
        y1="8"
        x2="20"
        y2="8"
        className="stroke-slate-400"
        strokeWidth="2"
        strokeLinecap="round"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity }}
      />
      <motion.line
        x1="4"
        y1="12"
        x2="20"
        y2="12"
        className="stroke-slate-400"
        strokeWidth="2"
        strokeLinecap="round"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
      />
      <motion.line
        x1="4"
        y1="16"
        x2="20"
        y2="16"
        className="stroke-slate-400"
        strokeWidth="2"
        strokeLinecap="round"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, delay: 0.6 }}
      />
    </svg>
  );
}

function DrizzleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M18 13a3 3 0 100-6h-.5a4 4 0 00-7.5 0 3 3 0 100 6h8z"
        className="fill-slate-400"
      />
      {[6, 10, 14, 18].map((x, i) => (
        <motion.line
          key={x}
          x1={x}
          y1="16"
          x2={x}
          y2="18"
          className="stroke-blue-400"
          strokeWidth="2"
          strokeLinecap="round"
          animate={{ y1: [16, 17, 16], y2: [18, 19, 18], opacity: [1, 0.5, 1] }}
          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </svg>
  );
}

function RainIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M18 11a3 3 0 100-6h-.5a4 4 0 00-7.5 0 3 3 0 100 6h8z"
        className="fill-slate-400"
      />
      {[6, 10, 14, 18].map((x, i) => (
        <motion.line
          key={x}
          x1={x}
          y1="14"
          x2={x}
          y2="20"
          className="stroke-blue-500"
          strokeWidth="2"
          strokeLinecap="round"
          animate={{ y1: [14, 15, 14], y2: [20, 21, 20], opacity: [1, 0.3, 1] }}
          transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
    </svg>
  );
}

function HeavyRainIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M18 9a3 3 0 100-6h-.5a4 4 0 00-7.5 0 3 3 0 100 6h8z"
        className="fill-slate-500"
      />
      {[4, 7, 10, 13, 16, 19].map((x, i) => (
        <motion.line
          key={x}
          x1={x}
          y1="12"
          x2={x}
          y2="20"
          className="stroke-blue-600"
          strokeWidth="2.5"
          strokeLinecap="round"
          animate={{ y1: [12, 14, 12], y2: [20, 22, 20], opacity: [1, 0.2, 1] }}
          transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.1 }}
        />
      ))}
    </svg>
  );
}

function SnowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M18 11a3 3 0 100-6h-.5a4 4 0 00-7.5 0 3 3 0 100 6h8z"
        className="fill-slate-400"
      />
      {[6, 10, 14, 18].map((x, i) => (
        <motion.g
          key={x}
          animate={{ y: [0, 2, 0], opacity: [1, 0.3, 1] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3 }}
        >
          <circle cx={x} cy="16" r="1.5" className="fill-slate-300" />
        </motion.g>
      ))}
    </svg>
  );
}

function HeavySnowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M18 9a3 3 0 100-6h-.5a4 4 0 00-7.5 0 3 3 0 100 6h8z"
        className="fill-slate-500"
      />
      {[4, 8, 12, 16, 20].map((x, i) => (
        <motion.g
          key={x}
          animate={{ y: [0, 3, 0], opacity: [1, 0.2, 1] }}
          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
        >
          <circle cx={x} cy="14" r="2" className="fill-slate-200" />
          <circle cx={x + 2} cy="18" r="1.5" className="fill-slate-300" />
        </motion.g>
      ))}
    </svg>
  );
}

function ThunderstormIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M18 8a3 3 0 100-6h-.5a4 4 0 00-7.5 0 3 3 0 100 6h8z"
        className="fill-slate-600"
      />
      <motion.path
        d="M13 11l-2 4h3l-2 5 5-6h-3l2-3h-3z"
        className="fill-yellow-400"
        animate={{ opacity: [1, 0.5, 1] }}
        transition={{ duration: 0.3, repeat: Infinity }}
      />
      {[5, 9, 17].map((x, i) => (
        <motion.line
          key={x}
          x1={x}
          y1="14"
          x2={x}
          y2="18"
          className="stroke-blue-500"
          strokeWidth="1.5"
          strokeLinecap="round"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </svg>
  );
}

function UnknownIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="8" className="stroke-slate-400" strokeWidth="2" />
      <text x="12" y="16" textAnchor="middle" className="fill-slate-400 text-sm">?</text>
    </svg>
  );
}

// Wind direction arrow component
interface WindArrowProps {
  direction: number; // degrees
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function WindArrow({ direction, size = 'md', className }: WindArrowProps) {
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };
  
  return (
    <motion.svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn(sizeMap[size], className)}
      style={{ transform: `rotate(${direction}deg)` }}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
    >
      <path
        d="M12 4L12 20M12 4L8 8M12 4L16 8"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </motion.svg>
  );
}

// Track condition indicator
interface TrackConditionIndicatorProps {
  condition: 'dry' | 'wet' | 'intermediate' | 'risk_of_rain';
  size?: 'sm' | 'md' | 'lg';
}

const trackConditionConfig = {
  dry: { color: 'bg-orange-500', label: 'Dry', icon: '☀️' },
  wet: { color: 'bg-blue-500', label: 'Wet', icon: '🌧️' },
  intermediate: { color: 'bg-yellow-500', label: 'Intermediate', icon: '⛅' },
  risk_of_rain: { color: 'bg-gray-400', label: 'Risk of Rain', icon: '⛈️' },
};

export function TrackConditionIndicator({ condition, size = 'md' }: TrackConditionIndicatorProps) {
  const config = trackConditionConfig[condition];
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium text-white',
        config.color,
        sizeClasses[size]
      )}
    >
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </motion.div>
  );
}

export default WeatherIcon;
