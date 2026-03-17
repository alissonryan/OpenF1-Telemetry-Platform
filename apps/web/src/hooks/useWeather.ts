'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  WeatherData,
  CurrentWeather,
  HourlyForecast,
  DailyForecast,
  WeatherConditions,
} from '@/types/weather';
import {
  getWeatherDescription,
  getTrackCondition,
} from '@/types/weather';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseWeatherOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
  enabled?: boolean;
}

interface UseWeatherReturn {
  // Data
  weather: WeatherData | null;
  current: CurrentWeather | null;
  hourlyForecast: HourlyForecast[];
  dailyForecast: DailyForecast[];
  conditions: WeatherConditions | null;
  
  // Loading states
  isLoading: boolean;
  isRefreshing: boolean;
  
  // Errors
  error: string | null;
  
  // Actions
  fetchByCoordinates: (lat: number, lon: number) => Promise<void>;
  fetchByCircuit: (circuitName: string) => Promise<void>;
  refresh: () => Promise<void>;
  
  // Status
  lastUpdate: number | null;
}

// Cache for weather data
const weatherCache = new Map<string, { data: WeatherData; timestamp: number }>();
const CACHE_TTL = 55 * 1000; // 55 seconds (refresh every 60s)

export function useWeather(options: UseWeatherOptions = {}): UseWeatherReturn {
  const {
    autoRefresh = true,
    refreshInterval = 60000, // 60 seconds
    enabled = true,
  } = options;
  
  // State
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  
  // Refs
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentLocationRef = useRef<{ type: 'coords' | 'circuit'; lat?: number; lon?: number; circuit?: string } | null>(null);
  
  // Parse current weather from API response
  const parseCurrentWeather = useCallback((data: Record<string, unknown>): CurrentWeather => {
    const current = data as Record<string, unknown>;
    const weatherCode = (current.weather_code as number) ?? 0;
    
    return {
      temperature: (current.temperature_2m as number) ?? (current.temperature as number) ?? 0,
      humidity: (current.relative_humidity_2m as number) ?? (current.humidity as number) ?? 0,
      wind_speed: (current.wind_speed_10m as number) ?? (current.wind_speed as number) ?? 0,
      wind_direction: (current.wind_direction_10m as number) ?? (current.wind_direction as number) ?? 0,
      wind_gusts: current.wind_gusts_10m as number | undefined,
      precipitation: (current.precipitation as number) ?? 0,
      weather_code: weatherCode,
      weather_description: getWeatherDescription(weatherCode),
      is_day: (current.is_day as number) === 1,
      time: (current.time as string) ?? new Date().toISOString(),
    };
  }, []);
  
  // Parse hourly forecast
  const parseHourlyForecast = useCallback((data: Record<string, unknown>): HourlyForecast[] => {
    const hourly = data as Record<string, unknown>;
    const times = (hourly.time as string[]) ?? [];
    const temps = (hourly.temperature_2m as number[]) ?? [];
    const precipProbs = (hourly.precipitation_probability as number[]) ?? [];
    const precipAmounts = (hourly.precipitation as number[]) ?? [];
    const weatherCodes = (hourly.weather_code as number[]) ?? [];
    const windSpeeds = (hourly.wind_speed_10m as number[]) ?? [];
    const windDirs = (hourly.wind_direction_10m as number[]) ?? [];
    const humidities = (hourly.relative_humidity_2m as number[]) ?? [];
    
    const result: HourlyForecast[] = [];
    const now = new Date();
    
    for (let i = 0; i < Math.min(times.length, 24); i++) {
      const time = new Date(times[i]);
      // Only include future hours
      if (time >= now) {
        const weatherCode = weatherCodes[i] ?? 0;
        result.push({
          date: times[i],
          hour: time.getHours(),
          temp: temps[i] ?? 0,
          temp_max: temps[i] ?? 0,
          temp_min: temps[i] ?? 0,
          precipitation_probability: precipProbs[i] ?? 0,
          precipitation_amount: precipAmounts[i] ?? 0,
          weather_code: weatherCode,
          weather_description: getWeatherDescription(weatherCode),
          wind_speed: windSpeeds[i] ?? 0,
          wind_direction: windDirs[i] ?? 0,
          humidity: humidities[i] ?? 0,
        });
      }
    }
    
    return result.slice(0, 8); // Return next 8 hours
  }, []);
  
  // Parse daily forecast
  const parseDailyForecast = useCallback((data: Record<string, unknown>): DailyForecast[] => {
    const daily = data as Record<string, unknown>;
    const times = (daily.time as string[]) ?? [];
    const maxTemps = (daily.temperature_2m_max as number[]) ?? [];
    const minTemps = (daily.temperature_2m_min as number[]) ?? [];
    const precipProbs = (daily.precipitation_probability_max as number[]) ?? [];
    const precipSums = (daily.precipitation_sum as number[]) ?? [];
    const weatherCodes = (daily.weather_code as number[]) ?? [];
    const windSpeeds = (daily.wind_speed_10m_max as number[]) ?? [];
    const windGusts = (daily.wind_gusts_10m_max as number[]) ?? [];
    const windDirs = (daily.wind_direction_10m_dominant as number[]) ?? [];
    const sunrises = (daily.sunrise as string[]) ?? [];
    const sunsets = (daily.sunset as string[]) ?? [];
    
    const result: DailyForecast[] = [];
    
    for (let i = 0; i < Math.min(times.length, 7); i++) {
      const weatherCode = weatherCodes[i] ?? 0;
      result.push({
        date: times[i],
        temp_max: maxTemps[i] ?? 0,
        temp_min: minTemps[i] ?? 0,
        precipitation_probability: precipProbs[i] ?? 0,
        precipitation_sum: precipSums[i] ?? 0,
        weather_code: weatherCode,
        weather_description: getWeatherDescription(weatherCode),
        wind_speed_max: windSpeeds[i] ?? 0,
        wind_gusts_max: windGusts[i],
        wind_direction: windDirs[i] ?? 0,
        sunrise: sunrises[i],
        sunset: sunsets[i],
      });
    }
    
    return result;
  }, []);
  
  // Calculate weather conditions for racing
  const calculateConditions = useCallback((): WeatherConditions | null => {
    if (!weather?.current) return null;
    
    const trackCondition = getTrackCondition(
      weather.current.weather_code,
      weather.current.precipitation,
      weather.forecast.hourly[0]?.precipitation_probability ?? 0
    );
    
    const visibilityGood = ![45, 48].includes(weather.current.weather_code);
    
    let windImpact: 'low' | 'medium' | 'high' = 'low';
    const windSpeed = weather.current.wind_speed;
    if (windSpeed > 40) {
      windImpact = 'high';
    } else if (windSpeed > 20) {
      windImpact = 'medium';
    }
    
    return {
      trackCondition,
      visibilityGood,
      windImpact,
      rainProbability: weather.forecast.hourly[0]?.precipitation_probability ?? 0,
    };
  }, [weather]);
  
  // Fetch weather by coordinates
  const fetchByCoordinates = useCallback(async (lat: number, lon: number) => {
    const cacheKey = `coords_${lat}_${lon}`;
    
    // Check cache
    const cached = weatherCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      setWeather(cached.data);
      setLastUpdate(cached.timestamp);
      return;
    }
    
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    
    setIsLoading(true);
    setError(null);
    currentLocationRef.current = { type: 'coords', lat, lon };
    
    try {
      const response = await fetch(
        `${API_BASE}/api/weather/current?latitude=${lat}&longitude=${lon}`,
        { signal: abortControllerRef.current.signal }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      const weatherData: WeatherData = {
        coordinates: { latitude: lat, longitude: lon },
        current: parseCurrentWeather(data.current),
        forecast: {
          hourly: [],
          daily: [],
        },
      };
      
      // Also fetch forecast
      try {
        const forecastResponse = await fetch(
          `${API_BASE}/api/weather/forecast?latitude=${lat}&longitude=${lon}&days=7`
        );
        
        if (forecastResponse.ok) {
          const forecastData = await forecastResponse.json();
          weatherData.forecast = {
            hourly: parseHourlyForecast(forecastData.hourly ?? {}),
            daily: parseDailyForecast(forecastData.daily ?? {}),
          };
        }
      } catch {
        // Non-critical, continue without forecast
      }
      
      // Update cache
      weatherCache.set(cacheKey, { data: weatherData, timestamp: Date.now() });
      
      setWeather(weatherData);
      setLastUpdate(Date.now());
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // Ignore abort errors
      }
      console.error('Failed to fetch weather:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch weather');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [parseCurrentWeather, parseHourlyForecast, parseDailyForecast]);
  
  // Fetch weather by circuit name
  const fetchByCircuit = useCallback(async (circuitName: string) => {
    const cacheKey = `circuit_${circuitName.toLowerCase()}`;
    
    // Check cache
    const cached = weatherCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      setWeather(cached.data);
      setLastUpdate(cached.timestamp);
      return;
    }
    
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    
    setIsLoading(true);
    setError(null);
    currentLocationRef.current = { type: 'circuit', circuit: circuitName };
    
    try {
      const response = await fetch(
        `${API_BASE}/api/weather/circuit/${encodeURIComponent(circuitName)}`,
        { signal: abortControllerRef.current.signal }
      );
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Circuit "${circuitName}" not found`);
        }
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      const weatherData: WeatherData = {
        circuit: data.circuit,
        coordinates: data.coordinates ?? { latitude: 0, longitude: 0 },
        current: parseCurrentWeather(data.current),
        forecast: {
          hourly: parseHourlyForecast(data.forecast?.hourly ?? {}),
          daily: parseDailyForecast(data.forecast?.daily ?? {}),
        },
      };
      
      // Update cache
      weatherCache.set(cacheKey, { data: weatherData, timestamp: Date.now() });
      
      setWeather(weatherData);
      setLastUpdate(Date.now());
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // Ignore abort errors
      }
      console.error('Failed to fetch circuit weather:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch weather');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [parseCurrentWeather, parseHourlyForecast, parseDailyForecast]);
  
  // Refresh current data
  const refresh = useCallback(async () => {
    if (!currentLocationRef.current) return;
    
    setIsRefreshing(true);
    
    const location = currentLocationRef.current;
    if (location.type === 'coords' && location.lat && location.lon) {
      // Clear cache to force refresh
      const cacheKey = `coords_${location.lat}_${location.lon}`;
      weatherCache.delete(cacheKey);
      await fetchByCoordinates(location.lat, location.lon);
    } else if (location.type === 'circuit' && location.circuit) {
      const cacheKey = `circuit_${location.circuit.toLowerCase()}`;
      weatherCache.delete(cacheKey);
      await fetchByCircuit(location.circuit);
    }
  }, [fetchByCoordinates, fetchByCircuit]);
  
  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh || !enabled || !currentLocationRef.current) return;
    
    const interval = setInterval(() => {
      refresh();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [autoRefresh, enabled, refreshInterval, refresh]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);
  
  // Calculate conditions when weather changes
  const conditions = calculateConditions();
  
  return {
    weather,
    current: weather?.current ?? null,
    hourlyForecast: weather?.forecast.hourly ?? [],
    dailyForecast: weather?.forecast.daily ?? [],
    conditions,
    isLoading,
    isRefreshing,
    error,
    fetchByCoordinates,
    fetchByCircuit,
    refresh,
    lastUpdate,
  };
}

export default useWeather;
