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
import PageHeader from '@/components/ui/PageHeader';
import useWebSocket from '@/hooks/useWebSocket';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

interface IntervalData {
  driver_number: number;
  gap_to_leader?: number | null;
  interval?: number | null;
  date: string;
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
  const [intervals, setIntervals] = useState<IntervalData[]>([]);
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // WebSocket connection
  const {
    isConnected,
    connectionState,
    telemetry,
    positions: livePositions,
    lastHeartbeat,
    subscribe,
    connect,
  } = useWebSocket({
    autoConnect: false,
    reconnectAttempts: 5,
  });

  // Fetch drivers when session changes (still use HTTP for initial load)
  useEffect(() => {
    if (!selectedSession) return;

    let isMounted = true;

    const loadSessionContext = async () => {
      setIsLoading(true);
      try {
        await Promise.all([fetchDrivers(), fetchSessionInfo(), fetchIntervals()]);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadSessionContext();

    return () => {
      isMounted = false;
    };
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

  useEffect(() => {
    if (livePositions.length > 0) {
      setPositions(livePositions);
    }
  }, [livePositions]);

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
      const response = await fetch(`${API_BASE}/api/sessions?session_key=${selectedSession}`);
      const payload = await response.json();
      const session = (payload.data ?? []).find((item: Session) => item.session_key === selectedSession);
      setSessionInfo(session || null);
    } catch (error) {
      console.error('Failed to fetch session info:', error);
    }
  };

  const fetchDrivers = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/telemetry/drivers?session_key=${selectedSession}`);
      const payload = await response.json();
      const driverList = payload.data ?? [];
      setDrivers(driverList);
      // Select first 3 drivers by default
      setSelectedDrivers(driverList.slice(0, 3).map((driver: Driver) => driver.driver_number));
    } catch (error) {
      console.error('Failed to fetch drivers:', error);
    }
  };

  const fetchPositions = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/telemetry/position?session_key=${selectedSession}&limit=100`
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

  const fetchIntervals = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/telemetry/intervals?session_key=${selectedSession}&limit=30`
      );
      const payload: IntervalData[] = await response.json();
      const latest = new Map<number, IntervalData>();
      payload.forEach((item) => {
        latest.set(item.driver_number, item);
      });
      setIntervals(Array.from(latest.values()));
    } catch (error) {
      console.error('Failed to fetch intervals:', error);
      setIntervals([]);
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
        <PageHeader
          eyebrow="Race Snapshot"
          title="F1 Telemetry Dashboard"
          description="Compact overview of the selected session with live map, key telemetry and a position table backed by real interval data."
          actions={
            <F1ConnectionIndicator 
              isConnected={isConnected} 
              connectionState={connectionState}
            />
          }
          className="mb-6"
        />

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
              className="mb-6 rounded-xl border border-white/5 bg-gray-900/50 p-6"
            >
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-f1-red text-xs font-bold text-white">3</span>
                <h2 className="text-xl font-semibold text-white">Select Drivers to Track</h2>
              </div>
              <p className="mb-6 text-sm text-gray-400">
                Click on the drivers below to monitor their live telemetry and track position.
              </p>
              
              {drivers.length === 0 ? (
                 <div className="flex h-32 flex-col items-center justify-center rounded-lg border border-dashed border-gray-700 bg-gray-800/30 text-gray-400">
                   <p>Loading drivers for this session...</p>
                 </div>
              ) : (
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
              )}
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
            {selectedDrivers.length > 0 ? (
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
                    selectedDrivers={selectedDrivers}
                    drivers={drivers}
                  />
                  <TelemetryChart
                    title="Throttle (%)"
                    data={telemetryData}
                    dataKey="throttle"
                    selectedDrivers={selectedDrivers}
                    drivers={drivers}
                  />
                  <TelemetryChart
                    title="Gear"
                    data={telemetryData}
                    dataKey="gear"
                    selectedDrivers={selectedDrivers}
                    drivers={drivers}
                  />
                  <TelemetryChart
                    title="RPM"
                    data={telemetryData}
                    dataKey="rpm"
                    selectedDrivers={selectedDrivers}
                    drivers={drivers}
                  />
                </div>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-700 bg-gray-900/40 py-16 text-center"
              >
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-800">
                  <svg className="h-8 w-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                  </svg>
                </div>
                <h3 className="text-xl font-medium text-white">No Drivers Selected</h3>
                <p className="mt-2 max-w-sm text-center text-sm text-gray-400">
                  Select up to 4 drivers from the list above to view their live telemetry and track positions.
                </p>
              </motion.div>
            )}

            {/* Leaderboard */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Leaderboard positions={positions} drivers={drivers} intervals={intervals} />
            </motion.div>
          </>
        )}

        {!selectedSession && !isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-700 bg-gray-900/40 px-6 py-24 text-center mt-8"
          >
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-gray-800/80 shadow-inner">
              <svg className="h-10 w-10 text-f1-red" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 className="mb-4 text-2xl font-bold text-white tracking-wide">Welcome to Live Telemetry</h2>
            <div className="max-w-md text-gray-400 space-y-4">
              <p>
                Follow the numbered steps at the top of the screen to begin:
              </p>
              <ol className="text-left space-y-4 mt-6">
                <li className="flex items-start gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-800 text-xs font-bold text-white">1</span>
                  <span className="text-sm">Select a <strong className="text-white">Meeting</strong> (e.g., Bahrain Grand Prix)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gray-800 text-xs font-bold text-white">2</span>
                  <span className="text-sm">Pick the specific <strong className="text-white">Session</strong> (e.g., Race, Qualifying) to connect to the telemetry stream.</span>
                </li>
              </ol>
            </div>
          </motion.div>
        )}
      </div>
    </Layout>
  );
}
