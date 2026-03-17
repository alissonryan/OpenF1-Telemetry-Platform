'use client';

import { useState, useEffect, useCallback } from 'react';
import useWebSocket from './useWebSocket';
import type {
  PitPrediction,
  DriverPositionForecast,
  StrategyAnalysis,
  PositionForecastResponse,
} from '@/types/predictions';

interface UsePredictionsOptions {
  sessionKey?: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
}

interface UsePredictionsReturn {
  // Data
  pitPredictions: Map<number, PitPrediction>;
  positionForecast: DriverPositionForecast[];
  strategies: Map<number, StrategyAnalysis>;
  
  // Loading states
  isLoadingPit: boolean;
  isLoadingPositions: boolean;
  isLoadingStrategy: boolean;
  
  // Errors
  pitError: string | null;
  positionError: string | null;
  strategyError: string | null;
  
  // Actions
  fetchPitPredictions: (driverNumbers?: number[]) => Promise<void>;
  fetchPositionForecast: (lapsAhead?: number) => Promise<void>;
  fetchStrategy: (driverNumber: number) => Promise<void>;
  fetchAllPredictions: () => Promise<void>;
  
  // Real-time status
  lastUpdate: number | null;
  isConnected: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getResponseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string') {
      return payload.detail;
    }
  } catch {
    // Fall back to the HTTP status text when the response body is not JSON.
  }

  return `HTTP ${response.status}`;
}

export function usePredictions(options: UsePredictionsOptions = {}): UsePredictionsReturn {
  const { sessionKey, autoRefresh = true, refreshInterval = 10000 } = options;
  
  // State
  const [pitPredictions, setPitPredictions] = useState<Map<number, PitPrediction>>(new Map());
  const [positionForecast, setPositionForecast] = useState<DriverPositionForecast[]>([]);
  const [strategies, setStrategies] = useState<Map<number, StrategyAnalysis>>(new Map());
  
  const [isLoadingPit, setIsLoadingPit] = useState(false);
  const [isLoadingPositions, setIsLoadingPositions] = useState(false);
  const [isLoadingStrategy, setIsLoadingStrategy] = useState(false);
  
  const [pitError, setPitError] = useState<string | null>(null);
  const [positionError, setPositionError] = useState<string | null>(null);
  const [strategyError, setStrategyError] = useState<string | null>(null);
  
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  
  // WebSocket for real-time updates
  const { isConnected, subscribe, connect } = useWebSocket({
    autoConnect: false,
    onMessage: (message) => {
      if (message.type === 'predictions' && message.data) {
          // Handle real-time prediction updates
          const payload = message.data as {
            pit_predictions?: PitPrediction[];
            position_forecast?: DriverPositionForecast[];
            strategies?: StrategyAnalysis[];
          };
          
          if (payload.pit_predictions) {
            setPitPredictions((previous) => {
              const next = new Map(previous);
              payload.pit_predictions!.forEach((pred) => {
                next.set(pred.driver_number, pred);
              });
              return next;
            });
          }
          
          if (payload.position_forecast) {
            setPositionForecast(payload.position_forecast);
          }

          if (payload.strategies) {
            setStrategies(() => {
              const next = new Map<number, StrategyAnalysis>();
              payload.strategies!.forEach((strategy) => {
                next.set(strategy.driver_number, strategy);
              });
              return next;
            });
          }
        
        setLastUpdate(Date.now());
      }
    },
  });
  
  // Fetch pit predictions
  const fetchPitPredictions = useCallback(async (driverNumbers?: number[]) => {
    if (!sessionKey) return;
    
    setIsLoadingPit(true);
    setPitError(null);
    
    try {
      const params = new URLSearchParams({
        session_key: sessionKey.toString(),
      });
      
      if (driverNumbers && driverNumbers.length > 0) {
        params.append('driver_numbers', driverNumbers.join(','));
      }
      
      const response = await fetch(`${API_BASE}/api/predictions/pit-stop/batch?${params}`);
      
      if (!response.ok) {
        throw new Error(await getResponseError(response));
      }
      
      const data: PitPrediction[] = await response.json();
      
      const newMap = new Map<number, PitPrediction>();
      data.forEach(pred => {
        newMap.set(pred.driver_number, pred);
      });
      
      setPitPredictions(newMap);
      setLastUpdate(Date.now());
    } catch (err) {
      console.error('Failed to fetch pit predictions:', err);
      setPitError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoadingPit(false);
    }
  }, [sessionKey]);
  
  // Fetch position forecast
  const fetchPositionForecast = useCallback(async (lapsAhead: number = 10) => {
    if (!sessionKey) return;
    
    setIsLoadingPositions(true);
    setPositionError(null);
    
    try {
      const params = new URLSearchParams({
        session_key: sessionKey.toString(),
        laps_ahead: lapsAhead.toString(),
      });
      
      const response = await fetch(`${API_BASE}/api/predictions/position-forecast?${params}`);
      
      if (!response.ok) {
        throw new Error(await getResponseError(response));
      }
      
      const data: PositionForecastResponse = await response.json();
      setPositionForecast(data.predictions);
      setLastUpdate(Date.now());
    } catch (err) {
      console.error('Failed to fetch position forecast:', err);
      setPositionError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoadingPositions(false);
    }
  }, [sessionKey]);
  
  // Fetch strategy for a driver
  const fetchStrategy = useCallback(async (_driverNumber: number) => {
    if (!sessionKey) return;
    
    setIsLoadingStrategy(true);
    setStrategyError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/predictions/strategy/batch?session_key=${sessionKey}`);
      
      if (!response.ok) {
        throw new Error(await getResponseError(response));
      }
      
      const data: StrategyAnalysis[] = await response.json();

      setStrategies((previous) => {
        const next = new Map(previous);
        data.forEach((strategy) => {
          next.set(strategy.driver_number, strategy);
        });
        return next;
      });
      setLastUpdate(Date.now());
    } catch (err) {
      console.error('Failed to fetch strategy:', err);
      setStrategyError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoadingStrategy(false);
    }
  }, [sessionKey]);
  
  // Fetch all predictions
  const fetchAllPredictions = useCallback(async () => {
    await fetchPitPredictions();
    await fetchPositionForecast();
    await fetchStrategy(0);
  }, [fetchPitPredictions, fetchPositionForecast, fetchStrategy]);
  
  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh || !sessionKey) return;
    
    // Initial fetch
    fetchAllPredictions();
    
    // Set up interval
    const interval = setInterval(fetchAllPredictions, refreshInterval);
    
    return () => clearInterval(interval);
  }, [autoRefresh, sessionKey, refreshInterval, fetchAllPredictions]);

  useEffect(() => {
    if (sessionKey) {
      connect();
    }
  }, [sessionKey, connect]);
  
  // Subscribe to WebSocket predictions channel
  useEffect(() => {
    if (sessionKey && isConnected) {
      subscribe({
        session_key: sessionKey,
        channels: ['predictions'],
      });
    }
  }, [sessionKey, isConnected, subscribe]);
  
  return {
    pitPredictions,
    positionForecast,
    strategies,
    isLoadingPit,
    isLoadingPositions,
    isLoadingStrategy,
    pitError,
    positionError,
    strategyError,
    fetchPitPredictions,
    fetchPositionForecast,
    fetchStrategy,
    fetchAllPredictions,
    lastUpdate,
    isConnected,
  };
}

export default usePredictions;
