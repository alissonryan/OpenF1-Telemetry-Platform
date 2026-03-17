import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseF1DataOptions {
  endpoint: string;
  params?: Record<string, string | number | boolean | null | undefined>;
  enabled?: boolean;
  refetchInterval?: number;
}

export function useF1Data<T>({
  endpoint,
  params = {},
  enabled = true,
  refetchInterval,
}: UseF1DataOptions) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = useCallback(async () => {
    if (!enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value));
        }
      });

      const url = `${API_BASE}${endpoint}?${searchParams.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('An error occurred'));
    } finally {
      setIsLoading(false);
    }
  }, [endpoint, params, enabled]);

  useEffect(() => {
    fetchData();

    if (refetchInterval && enabled) {
      const interval = setInterval(fetchData, refetchInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, refetchInterval, enabled]);

  return { data, error, isLoading, refetch: fetchData };
}

// Specialized hooks for common use cases
export function useMeetings(year?: number) {
  return useF1Data({
    endpoint: '/api/sessions/meetings',
    params: { year },
  });
}

export function useSessions(meetingKey?: number) {
  return useF1Data({
    endpoint: '/api/sessions',
    params: { meeting_key: meetingKey },
    enabled: !!meetingKey,
  });
}

export function useDrivers(sessionKey?: number) {
  return useF1Data({
    endpoint: '/api/telemetry/drivers',
    params: { session_key: sessionKey },
    enabled: !!sessionKey,
  });
}

export function useCarData(sessionKey?: number, driverNumber?: number, limit?: number) {
  return useF1Data({
    endpoint: '/api/telemetry/car-data',
    params: { session_key: sessionKey, driver_number: driverNumber, limit },
    enabled: !!sessionKey,
    refetchInterval: 1000, // Refetch every second for real-time data
  });
}

export function usePositions(sessionKey?: number, latest?: boolean) {
  return useF1Data({
    endpoint: '/api/telemetry/position',
    params: { session_key: sessionKey, latest },
    enabled: !!sessionKey,
    refetchInterval: 4000, // Positions update every 4 seconds
  });
}

export function useLaps(sessionKey?: number, driverNumber?: number, lapNumber?: number) {
  return useF1Data({
    endpoint: '/api/telemetry/laps',
    params: { session_key: sessionKey, driver_number: driverNumber, lap_number: lapNumber },
    enabled: !!sessionKey,
  });
}

export function useWeather(sessionKey?: number) {
  return useF1Data({
    endpoint: sessionKey ? `/api/sessions/${sessionKey}/weather` : '/api/sessions',
    enabled: !!sessionKey,
    refetchInterval: 60000, // Weather updates every minute
  });
}

export function usePitStops(sessionKey?: number) {
  return useF1Data({
    endpoint: sessionKey ? `/api/sessions/${sessionKey}/pit` : '/api/sessions',
    enabled: !!sessionKey,
  });
}
