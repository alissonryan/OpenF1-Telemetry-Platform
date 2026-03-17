'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SimpleSessionSelector from '@/components/dashboard/SimpleSessionSelector';
import SimpleDriverCard from '@/components/dashboard/SimpleDriverCard';
import TelemetryChart from '@/components/charts/TelemetryChart';
import Leaderboard from '@/components/dashboard/Leaderboard';
import TrackMap, { DriverPosition, DriverInfo } from '@/components/dashboard/TrackMap';
import WeatherWidget from '@/components/dashboard/WeatherWidget';
import ConnectionStatus, { F1ConnectionIndicator } from '@/components/ui/ConnectionStatus';
import useWebSocket from '@/hooks/useWebSocket';

interface Driver {
  driver_number: number;
  name_acronym: string;
  first_name: string;
  last_name: string;
  team_name: string;
  team_colour: string;
  country_code: string;
}

interface Position {
  position: number;
  date: string;
  driver_number: number;
  x?: number;
  y?: number;
  z?: number;
}

interface Session {
  session_key: number;
  meeting_key: number;
  location: string;
  session_type: string;
  session_name: string;
  circuit_key?: number;
  circuit_short_name?: string;
  country_name: string;
  date_start: string;
  date_end: string;
  year: number;
}

export default function DashboardPage() {
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [sessionInfo, setSessionInfo] = useState<Session | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // WebSocket connection
  const {
    isConnected,
    connectionState,
    telemetry,
    lastHeartbeat,
    subscribe,
    connect,
  } = useWebSocket({
    autoConnect: false,
    reconnectAttempts: 5,
  });

  // Fetch drivers when session changes (still use HTTP for initial load)
  useEffect(() => {
    if (selectedSession) {
      fetchDrivers();
      fetchSessionInfo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSession]);

  // Subscribe to WebSocket when session and drivers are selected
  useEffect(() => {
    if (selectedSession && selectedDrivers.length > 0 && isConnected) {
      subscribe({
        session_key: selectedSession,
        driver_numbers: selectedDrivers,
        channels: ['telemetry', 'positions', 'pit_stop', 'weather'],
      });
    }
  }, [selectedSession, selectedDrivers, isConnected, subscribe]);

  // Update positions from WebSocket
  useEffect(() => {
    if (positions.length === 0 && telemetry.size > 0) {
      // Fetch positions via HTTP as fallback
      fetchPositions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [telemetry]);

  // Convert WebSocket telemetry to chart format
  const telemetryData = telemetry;

  // Convert positions to track map format with normalized coordinates
  const trackMapPositions: DriverPosition[] = useMemo(() => {
    return positions.map(pos => {
      const telemetryData = telemetry.get(pos.driver_number);
      const latestTelemetry = telemetryData?.[telemetryData.length - 1];
      
      // Normalize x/y to 0-1000 scale (assuming OpenF1 API uses 1/10 meter units)
      // Real coordinates need to be normalized based on track bounds
      const x = pos.x ?? 500; // Default to center if no data
      const y = pos.y ?? 500;
      
      return {
        driver_number: pos.driver_number,
        x: x,
        y: y,
        z: pos.z,
        position: pos.position,
        speed: latestTelemetry?.speed,
        drs: latestTelemetry?.drs,
        date: pos.date,
      };
    });
  }, [positions, telemetry]);

  // Convert drivers to track map format
  const trackMapDrivers: DriverInfo[] = useMemo(() => {
    return drivers.map(driver => ({
      driver_number: driver.driver_number,
      name_acronym: driver.name_acronym,
      first_name: driver.first_name,
      last_name: driver.last_name,
      team_name: driver.team_name,
      team_colour: driver.team_colour,
    }));
  }, [drivers]);

  const fetchSessionInfo = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/telemetry/sessions`);
      const data = await response.json();
      const session = data.find((s: Session) => s.session_key === selectedSession);
      setSessionInfo(session || null);
    } catch (error) {
      console.error('Failed to fetch session info:', error);
    }
  };

  const fetchDrivers = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/telemetry/drivers?session_key=${selectedSession}`);
      const data = await response.json();
      setDrivers(data);
      // Select first 3 drivers by default
      setSelectedDrivers(data.slice(0, 3).map((d: Driver) => d.driver_number));
    } catch (error) {
      console.error('Failed to fetch drivers:', error);
    }
  };

  const fetchPositions = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/telemetry/position?session_key=${selectedSession}&limit=100`
      );
      const data = await response.json();
      
      // Get latest position for each driver
      const latestPositions: { [key: number]: Position } = {};
      data.data?.forEach((pos: Position) => {
        if (!latestPositions[pos.driver_number] || 
            new Date(pos.date) > new Date(latestPositions[pos.driver_number].date)) {
          latestPositions[pos.driver_number] = pos;
        }
      });
      
      setPositions(Object.values(latestPositions));
    } catch (error) {
      console.error('Failed to fetch positions:', error);
    }
  };

  const handleSessionSelect = (sessionKey: number) => {
    setSelectedSession(sessionKey);
    // Connect WebSocket if not connected
    if (!isConnected) {
      connect();
    }
  };

  const handleDriverToggle = (driverNumber: number) => {
    setSelectedDrivers((prev) => {
      const updated = prev.includes(driverNumber)
        ? prev.filter((d) => d !== driverNumber)
        : [...prev, driverNumber];
      
      // Re-subscribe with updated driver list
      if (selectedSession && isConnected) {
        subscribe({
          session_key: selectedSession,
          driver_numbers: updated,
          channels: ['telemetry', 'positions', 'pit_stop', 'weather'],
        });
      }
      
      return updated;
    });
  };

  const handleDriverClick = (driverNumber: number) => {
    // Toggle driver selection when clicking on track map
    handleDriverToggle(driverNumber);
  };

  return (
    <Layout>
      <div className="p-6">
        {/* Header with Connection Status */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6 flex items-center justify-between"
        >
          <h1 className="text-2xl font-bold text-white">F1 Telemetry Dashboard</h1>
          <F1ConnectionIndicator 
            isConnected={isConnected} 
            connectionState={connectionState}
          />
        </motion.div>

        {/* Session Selector */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mb-6"
        >
          <SimpleSessionSelector onSelect={handleSessionSelect} />
        </motion.div>

        {/* Connection Error Message */}
        <AnimatePresence>
          {!isConnected && selectedSession && connectionState === 'error' && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 rounded-lg bg-red-500/20 p-4 text-red-400"
            >
              <div className="flex items-center gap-2">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>WebSocket connection failed. Real-time data unavailable.</span>
                <button
                  onClick={() => connect()}
                  className="ml-auto rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
                >
                  Retry
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {isLoading && (
          <div className="flex h-64 items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="h-12 w-12 rounded-full border-4 border-f1-red border-t-transparent"
            />
          </div>
        )}

        {selectedSession && !isLoading && (
          <>
            {/* Driver Cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mb-6"
            >
              <h2 className="mb-4 text-xl font-semibold text-white">Drivers</h2>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-5">
                {drivers.map((driver, index) => (
                  <motion.div
                    key={driver.driver_number}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <SimpleDriverCard
                      driver={driver}
                      isSelected={selectedDrivers.includes(driver.driver_number)}
                      onToggle={() => handleDriverToggle(driver.driver_number)}
                    />
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Live Data Indicator */}
            {isConnected && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-4 flex items-center gap-2 text-sm text-gray-400"
              >
                <ConnectionStatus
                  isConnected={isConnected}
                  connectionState={connectionState}
                  lastHeartbeat={lastHeartbeat}
                  showDetails
                />
                <span className="text-gray-500">|</span>
                <span>Streaming at ~3.7Hz</span>
              </motion.div>
            )}

            {/* Track Map, Weather and Telemetry Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-3"
            >
              {/* Track Map - Takes 1 column on large screens */}
              <div className="lg:col-span-1 space-y-4">
                <h2 className="text-xl font-semibold text-white">Track Map</h2>
                <TrackMap
                  circuitName={sessionInfo?.circuit_short_name || sessionInfo?.location}
                  positions={trackMapPositions}
                  drivers={trackMapDrivers}
                  selectedDrivers={selectedDrivers}
                  onDriverClick={handleDriverClick}
                  showDRSZones={true}
                  showSectors={true}
                  size="md"
                  className="aspect-square"
                />
                {/* Weather Widget below Track Map */}
                <WeatherWidget
                  circuitName={sessionInfo?.circuit_short_name || sessionInfo?.location}
                  autoRefresh={true}
                  compact={false}
                />
              </div>

              {/* Telemetry Charts - Takes 2 columns on large screens */}
              <div className="lg:col-span-2 grid grid-cols-1 gap-6 md:grid-cols-2">
                <TelemetryChart
                  title="Speed (km/h)"
                  data={telemetryData}
                  dataKey="speed"
                  color="#e10600"
                  selectedDrivers={selectedDrivers}
                  drivers={drivers}
                />
                <TelemetryChart
                  title="Throttle (%)"
                  data={telemetryData}
                  dataKey="throttle"
                  color="#00d2be"
                  selectedDrivers={selectedDrivers}
                  drivers={drivers}
                />
                <TelemetryChart
                  title="Brake"
                  data={telemetryData}
                  dataKey="brake"
                  color="#ff8700"
                  selectedDrivers={selectedDrivers}
                  drivers={drivers}
                />
                <TelemetryChart
                  title="RPM"
                  data={telemetryData}
                  dataKey="rpm"
                  color="#871aff"
                  selectedDrivers={selectedDrivers}
                  drivers={drivers}
                />
              </div>
            </motion.div>

            {/* Leaderboard */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Leaderboard positions={positions} drivers={drivers} />
            </motion.div>
          </>
        )}

        {!selectedSession && !isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex h-96 flex-col items-center justify-center text-gray-400"
          >
            <svg
              className="mb-4 h-24 w-24 text-gray-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <p className="text-xl">Select a session to view telemetry data</p>
            <p className="mt-2 text-sm text-gray-500">
              Real-time data will stream via WebSocket
            </p>
          </motion.div>
        )}
      </div>
    </Layout>
  );
}
