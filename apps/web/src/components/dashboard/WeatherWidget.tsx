'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import useWeather from '@/hooks/useWeather';
import { WeatherIcon, WindArrow, TrackConditionIndicator } from '@/components/weather/WeatherIcons';
import { getWindDirection } from '@/types/weather';
import type { HourlyForecast } from '@/types/weather';

interface WeatherWidgetProps {
  circuitName?: string;
  latitude?: number;
  longitude?: number;
  autoRefresh?: boolean;
  compact?: boolean;
  className?: string;
}

export default function WeatherWidget({
  circuitName,
  latitude,
  longitude,
  autoRefresh = true,
  compact = false,
  className,
}: WeatherWidgetProps) {
  const {
    current,
    hourlyForecast,
    conditions,
    isLoading,
    isRefreshing,
    error,
    fetchByCircuit,
    fetchByCoordinates,
    lastUpdate,
  } = useWeather({
    autoRefresh,
    refreshInterval: 60000,
    enabled: !!(circuitName || (latitude && longitude)),
  });

  // Fetch weather when props change
  useEffect(() => {
    if (circuitName) {
      fetchByCircuit(circuitName);
    } else if (latitude && longitude) {
      fetchByCoordinates(latitude, longitude);
    }
  }, [circuitName, latitude, longitude, fetchByCircuit, fetchByCoordinates]);

  // Loading skeleton
  if (isLoading && !current) {
    return <WeatherWidgetSkeleton compact={compact} className={className} />;
  }

  // Error state
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={cn(
          'rounded-xl border border-red-500/30 bg-red-500/10 p-4',
          compact ? 'w-full' : 'w-full max-w-md',
          className
        )}
      >
        <p className="text-sm text-red-400">{error}</p>
      </motion.div>
    );
  }

  // No data yet
  if (!current) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'overflow-hidden rounded-xl border border-white/10 bg-gray-900/80 backdrop-blur',
        compact ? 'p-3' : 'p-4',
        compact ? 'w-full' : 'w-full max-w-md',
        className
      )}
    >
      {/* Header */}
      <div className={cn('flex items-center justify-between', compact ? 'mb-2' : 'mb-4')}>
        <div className="flex items-center gap-2">
          <h3 className={cn('font-semibold text-white', compact ? 'text-sm' : 'text-base')}>
            Weather {circuitName && `- ${circuitName}`}
          </h3>
          {isRefreshing && (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="h-3 w-3 rounded-full border-2 border-f1-red border-t-transparent"
            />
          )}
        </div>
        {lastUpdate && (
          <span className="text-xs text-gray-500">
            {new Date(lastUpdate).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Main Weather Info */}
      <div className={cn('flex', compact ? 'gap-3' : 'gap-4')}>
        {/* Weather Icon and Temperature */}
        <div className="flex flex-col items-center">
          <WeatherIcon
            code={current.weather_code}
            size={compact ? 'md' : 'xl'}
            isNight={!current.is_day}
          />
          <motion.p
            key={current.temperature}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={cn('font-bold text-white', compact ? 'text-2xl' : 'text-4xl')}
          >
            {Math.round(current.temperature)}°
          </motion.p>
          <p className="text-xs text-gray-400">{current.weather_description}</p>
        </div>

        {/* Weather Details */}
        <div className={cn('flex-1', compact ? 'space-y-1' : 'space-y-2')}>
          {/* Humidity */}
          <WeatherDetailRow
            icon={<HumidityIcon />}
            label="Humidity"
            value={`${current.humidity}%`}
            compact={compact}
          />

          {/* Wind */}
          <WeatherDetailRow
            icon={
              <WindArrow direction={current.wind_direction} size={compact ? 'sm' : 'md'} />
            }
            label="Wind"
            value={`${Math.round(current.wind_speed)} km/h ${getWindDirection(current.wind_direction)}`}
            compact={compact}
          />

          {/* Precipitation */}
          {current.precipitation > 0 && (
            <WeatherDetailRow
              icon={<RainIcon />}
              label="Rain"
              value={`${current.precipitation.toFixed(1)} mm`}
              compact={compact}
            />
          )}

          {/* Track Condition */}
          {conditions && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="pt-1"
            >
              <TrackConditionIndicator
                condition={conditions.trackCondition}
                size={compact ? 'sm' : 'md'}
              />
            </motion.div>
          )}
        </div>
      </div>

      {/* Hourly Forecast (only if not compact) */}
      {!compact && hourlyForecast.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-4 border-t border-white/10 pt-4"
        >
          <h4 className="mb-2 text-xs font-medium text-gray-400">Next Hours</h4>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {hourlyForecast.slice(0, 6).map((hour, index) => (
              <HourlyForecastCard key={hour.date} hour={hour} index={index} />
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

// Weather detail row component
interface WeatherDetailRowProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  compact?: boolean;
}

function WeatherDetailRow({ icon, label, value, compact }: WeatherDetailRowProps) {
  return (
    <div className={cn('flex items-center gap-2', compact ? 'text-xs' : 'text-sm')}>
      <span className="text-gray-400">{icon}</span>
      <span className="text-gray-500">{label}:</span>
      <motion.span
        key={value}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-medium text-white"
      >
        {value}
      </motion.span>
    </div>
  );
}

// Hourly forecast card component
interface HourlyForecastCardProps {
  hour: HourlyForecast;
  index: number;
}

function HourlyForecastCard({ hour, index }: HourlyForecastCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex min-w-[60px] flex-col items-center rounded-lg bg-white/5 p-2"
    >
      <span className="text-xs text-gray-400">
        {hour.hour.toString().padStart(2, '0')}:00
      </span>
      <WeatherIcon code={hour.weather_code} size="sm" />
      <span className="text-sm font-medium text-white">{Math.round(hour.temp)}°</span>
      {hour.precipitation_probability > 20 && (
        <span className="text-xs text-blue-400">
          {hour.precipitation_probability}%
        </span>
      )}
    </motion.div>
  );
}

// Skeleton loader
interface WeatherWidgetSkeletonProps {
  compact?: boolean;
  className?: string;
}

export function WeatherWidgetSkeleton({ compact, className }: WeatherWidgetSkeletonProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn(
        'rounded-xl border border-white/10 bg-gray-900/80 p-4',
        compact ? 'w-full' : 'w-full max-w-md',
        className
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="h-4 w-24 animate-pulse rounded bg-gray-700" />
        <div className="h-3 w-12 animate-pulse rounded bg-gray-700" />
      </div>
      <div className="flex gap-4">
        <div className="flex flex-col items-center gap-2">
          <div className={cn('animate-pulse rounded bg-gray-700', compact ? 'h-8 w-8' : 'h-16 w-16')} />
          <div className={cn('animate-pulse rounded bg-gray-700', compact ? 'h-6 w-10' : 'h-10 w-16')} />
        </div>
        <div className="flex-1 space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-4 w-full animate-pulse rounded bg-gray-700" />
          ))}
        </div>
      </div>
      {!compact && (
        <div className="mt-4 flex gap-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 w-14 animate-pulse rounded bg-gray-700" />
          ))}
        </div>
      )}
    </motion.div>
  );
}

// Icon components
function HumidityIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0z"
        className="stroke-current"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}

function RainIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M16 13v8M8 13v8M12 15v8"
        className="stroke-blue-400"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

// Compact weather badge for inline use
interface WeatherBadgeProps {
  circuitName?: string;
  className?: string;
}

export function WeatherBadge({ circuitName, className }: WeatherBadgeProps) {
  const { current, isLoading, fetchByCircuit } = useWeather({
    autoRefresh: true,
    enabled: !!circuitName,
  });

  useEffect(() => {
    if (circuitName) {
      fetchByCircuit(circuitName);
    }
  }, [circuitName, fetchByCircuit]);

  if (isLoading || !current) {
    return (
      <span className={cn('inline-flex items-center gap-1 text-xs text-gray-400', className)}>
        <div className="h-3 w-3 animate-pulse rounded bg-gray-600" />
        Loading...
      </span>
    );
  }

  return (
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn('inline-flex items-center gap-1.5 text-sm', className)}
    >
      <WeatherIcon code={current.weather_code} size="sm" />
      <span className="font-medium text-white">{Math.round(current.temperature)}°C</span>
      <span className="text-gray-400">{current.weather_description}</span>
    </motion.span>
  );
}

export { WeatherWidget };
