/**
 * WebSocket hook for real-time F1 telemetry data.
 * 
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Connection state management
 * - Message parsing and type safety
 * - Buffer for recent data
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ==================== Types ====================

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketMessage {
  type: string;
  data?: unknown;
  timestamp?: number;
  driver_number?: number;
  message?: string;
}

export interface TelemetryData {
  speed: number;
  throttle: number;
  brake: number;
  gear: number;
  rpm: number;
  drs: number;
  date: string;
  driver_number: number;
}

export interface PositionData {
  position: number;
  date: string;
  driver_number: number;
  x?: number;
  y?: number;
  z?: number;
}

export interface PitStopData {
  driver_number: number;
  lap_number: number;
  pit_duration?: number;
  date?: string;
}

export interface WeatherData {
  air_temperature?: number;
  track_temperature?: number;
  humidity?: number;
  pressure?: number;
  rainfall?: number;
  wind_speed?: number;
  wind_direction?: number;
}

export interface SubscriptionOptions {
  session_key?: number;
  driver_numbers?: number[];
  channels?: string[];
}

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  connectionState: ConnectionState;
  isConnected: boolean;
  telemetry: Map<number, TelemetryData[]>;
  positions: PositionData[];
  pitStops: Map<number, PitStopData>;
  weather: WeatherData | null;
  lastHeartbeat: number | null;
  subscribe: (options: SubscriptionOptions) => void;
  unsubscribe: (channels: string[]) => void;
  ping: () => void;
  getBuffer: (driverNumber: number) => TelemetryData[] | undefined;
  connect: () => void;
  disconnect: () => void;
  error: string | null;
}

// ==================== Hook ====================

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    autoConnect = true,
    reconnectAttempts = 10,
    reconnectInterval = 1000,
    maxReconnectInterval = 30000,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  // State
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [telemetry, setTelemetry] = useState<Map<number, TelemetryData[]>>(new Map());
  const [positions, setPositions] = useState<PositionData[]>([]);
  const [pitStops, setPitStops] = useState<Map<number, PitStopData>>(new Map());
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);
  const bufferRef = useRef<Map<number, TelemetryData[]>>(new Map());

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Calculate backoff interval
  const getBackoffInterval = useCallback(() => {
    const backoff = Math.min(
      reconnectInterval * Math.pow(2, reconnectCountRef.current),
      maxReconnectInterval
    );
    // Add jitter
    return backoff + Math.random() * 1000;
  }, [reconnectInterval, maxReconnectInterval]);

  // Handle incoming message
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Clear error on successful message
      setError(null);

      switch (message.type) {
        case 'telemetry':
          if (message.data && message.driver_number) {
            const driverNumber = message.driver_number;
            const newData = Array.isArray(message.data) ? message.data : [message.data];
            
            setTelemetry((prev) => {
              const updated = new Map(prev);
              const existing = updated.get(driverNumber) || [];
              // Keep last 100 data points
              updated.set(driverNumber, [...existing, ...newData].slice(-100));
              return updated;
            });
            
            // Update buffer ref
            bufferRef.current.set(
              driverNumber,
              [...(bufferRef.current.get(driverNumber) || []), ...newData].slice(-200)
            );
          }
          break;

        case 'positions':
          if (message.data) {
            setPositions(Array.isArray(message.data) ? message.data : [message.data]);
          }
          break;

        case 'pit_stop':
          if (message.data) {
            setPitStops((prev) => {
              const updated = new Map(prev);
              const pitData = message.data as Record<string, unknown>;
              if (pitData.driver_number) {
                updated.set(pitData.driver_number as number, pitData as unknown as PitStopData);
              } else if (typeof pitData === 'object') {
                // Handle object with driver numbers as keys
                Object.entries(pitData).forEach(([driverNum, data]) => {
                  updated.set(Number(driverNum), data as PitStopData);
                });
              }
              return updated;
            });
          }
          break;

        case 'weather':
          if (message.data) {
            setWeather(message.data);
          }
          break;

        case 'heartbeat':
          setLastHeartbeat(message.timestamp || Date.now());
          break;

        case 'pong':
          // Ping response
          break;

        case 'subscribed':
          // console.log('Subscribed:', message);
          break;

        case 'unsubscribed':
          // console.log('Unsubscribed:', message);
          break;

        case 'error':
          setError(message.message || 'Unknown error');
          // console.error('WebSocket error:', message.message);
          break;

        default:
          // console.log('Unknown message type:', message.type);
      }

      // Call custom message handler
      onMessage?.(message);
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  }, [onMessage]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    clearReconnectTimeout();
    setConnectionState('connecting');
    setError(null);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        // console.log('WebSocket connected');
        setConnectionState('connected');
        setError(null);
        reconnectCountRef.current = 0;
        shouldReconnectRef.current = true;
        onConnect?.();
      };

      ws.onmessage = handleMessage;

      ws.onclose = () => {
        // console.log('WebSocket closed:', event.code, event.reason);
        setConnectionState('disconnected');
        onDisconnect?.();

        // Attempt reconnect
        if (
          shouldReconnectRef.current &&
          reconnectCountRef.current < reconnectAttempts
        ) {
          const interval = getBackoffInterval();
          // console.log(`Reconnecting in ${interval}ms (attempt ${reconnectCountRef.current + 1}/${reconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectCountRef.current++;
            connect();
          }, interval);
        } else if (reconnectCountRef.current >= reconnectAttempts) {
          setError('Max reconnection attempts reached');
          setConnectionState('error');
        }
      };

      ws.onerror = (event) => {
        // console.error('WebSocket error:', event);
        setError('Connection error');
        setConnectionState('error');
        onError?.(event);
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to create connection');
      setConnectionState('error');
    }
  }, [url, reconnectAttempts, getBackoffInterval, clearReconnectTimeout, handleMessage, onConnect, onDisconnect, onError]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    clearReconnectTimeout();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setConnectionState('disconnected');
  }, [clearReconnectTimeout]);

  // Subscribe to channels
  const subscribe = useCallback((options: SubscriptionOptions) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot subscribe');
      return;
    }

    const message = {
      command: 'subscribe',
      session_key: options.session_key,
      driver_numbers: options.driver_numbers || [],
      channels: options.channels || ['telemetry', 'positions', 'pit_stop', 'weather'],
    };

    wsRef.current.send(JSON.stringify(message));
  }, []);

  // Unsubscribe from channels
  const unsubscribe = useCallback((channels: string[]) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      return;
    }

    const message = {
      command: 'unsubscribe',
      channels,
    };

    wsRef.current.send(JSON.stringify(message));
  }, []);

  // Send ping
  const ping = useCallback(() => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(JSON.stringify({ command: 'ping' }));
  }, []);

  // Get buffered data
  const getBuffer = useCallback((driverNumber: number): TelemetryData[] | undefined => {
    return bufferRef.current.get(driverNumber);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (!autoConnect) {
      return;
    }

    connect();
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    telemetry,
    positions,
    pitStops,
    weather,
    lastHeartbeat,
    subscribe,
    unsubscribe,
    ping,
    getBuffer,
    connect,
    disconnect,
    error,
  };
}

// ==================== Specialized Hooks ====================

/**
 * Hook for telemetry data only
 */
export function useTelemetry(sessionKey?: number, driverNumbers?: number[]) {
  const { telemetry, connectionState, subscribe, isConnected } = useWebSocket({
    autoConnect: !!sessionKey,
  });

  useEffect(() => {
    if (sessionKey && isConnected) {
      subscribe({
        session_key: sessionKey,
        driver_numbers: driverNumbers,
        channels: ['telemetry'],
      });
    }
  }, [sessionKey, driverNumbers, isConnected, subscribe]);

  return { telemetry, connectionState, isConnected };
}

/**
 * Hook for positions data only
 */
export function usePositions(sessionKey?: number) {
  const [positions, setPositions] = useState<PositionData[]>([]);
  const { connectionState, subscribe, isConnected } = useWebSocket({
    autoConnect: !!sessionKey,
    onMessage: (message) => {
      if (message.type === 'positions' && message.data) {
        setPositions(Array.isArray(message.data) ? message.data : [message.data]);
      }
    },
  });

  useEffect(() => {
    if (sessionKey && isConnected) {
      subscribe({
        session_key: sessionKey,
        channels: ['positions'],
      });
    }
  }, [sessionKey, isConnected, subscribe]);

  return { positions, connectionState, isConnected };
}

export default useWebSocket;
