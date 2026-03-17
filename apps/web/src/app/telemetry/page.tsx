'use client';

import { useEffect, useMemo, useState } from 'react';
import Layout from '@/components/layout/Layout';
import TelemetryChart from '@/components/charts/TelemetryChart';
import Leaderboard from '@/components/dashboard/Leaderboard';
import SimpleDriverCard from '@/components/dashboard/SimpleDriverCard';
import SimpleSessionSelector from '@/components/dashboard/SimpleSessionSelector';
import TrackMap, {
  type DriverInfo,
  type DriverPosition,
} from '@/components/dashboard/TrackMap';
import WeatherWidget from '@/components/dashboard/WeatherWidget';
import ConnectionStatus from '@/components/ui/ConnectionStatus';
import PageHeader from '@/components/ui/PageHeader';
import { EmptyState, StatCard, Surface } from '@/components/ui/Surface';
import useWebSocket, {
  type PositionData as LivePositionData,
  type TelemetryData as LiveTelemetryData,
} from '@/hooks/useWebSocket';
import { apiFetch, ApiError } from '@/lib/api';
import { getDriverNameParts } from '@/lib/driver';
import type { Driver } from '@/types/telemetry';

interface LiveSessionInfo {
  session_key: number;
  meeting_key: number;
  location: string;
  session_type: string;
  session_name: string;
  circuit_short_name: string;
  country_name: string;
  date_start: string;
  date_end?: string | null;
  year: number;
}

interface IntervalData {
  driver_number: number;
  gap_to_leader?: number | null;
  interval?: number | null;
  date: string;
}

interface RaceControlMessage {
  date: string;
  category?: string | null;
  message?: string | null;
  flag?: string | null;
  scope?: string | null;
  driver_number?: number | null;
}

interface FastestLapPayload {
  driver_number?: number;
  lap_number?: number;
  lap_duration?: number;
}

interface PositionResponse {
  data: LivePositionData[];
}

interface DriverResponse {
  data: Driver[];
}

interface SessionResponse {
  data: LiveSessionInfo[];
}

export default function TelemetryPage() {
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [sessionInfo, setSessionInfo] = useState<LiveSessionInfo | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [positions, setPositions] = useState<LivePositionData[]>([]);
  const [intervals, setIntervals] = useState<IntervalData[]>([]);
  const [raceControl, setRaceControl] = useState<RaceControlMessage[]>([]);
  const [fastestLap, setFastestLap] = useState<FastestLapPayload | null>(null);
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  const {
    telemetry,
    positions: livePositions,
    connectionState,
    isConnected,
    subscribe,
    connect,
    lastHeartbeat,
  } = useWebSocket({
    autoConnect: false,
    reconnectAttempts: 5,
  });

  useEffect(() => {
    if (!selectedSession) {
      return;
    }

    let isMounted = true;

    const loadContext = async () => {
      setIsLoading(true);
      setPageError(null);
      try {
        const [
          sessionPayload,
          driverPayload,
          positionPayload,
          intervalPayload,
          raceControlPayload,
          fastestLapPayload,
        ] = await Promise.all([
          apiFetch<SessionResponse>('/api/sessions', {
            params: { session_key: selectedSession },
          }),
          apiFetch<DriverResponse>('/api/telemetry/drivers', {
            params: { session_key: selectedSession },
          }),
          apiFetch<PositionResponse>('/api/telemetry/position', {
            params: { session_key: selectedSession, limit: 100 },
          }),
          apiFetch<IntervalData[]>('/api/telemetry/intervals', {
            params: { session_key: selectedSession, limit: 30 },
          }),
          apiFetch<RaceControlMessage[]>(
            `/api/sessions/${selectedSession}/race-control`
          ),
          apiFetch<FastestLapPayload>('/api/telemetry/fastest-lap', {
            params: { session_key: selectedSession },
          }),
        ]);

        if (!isMounted) {
          return;
        }

        const session = sessionPayload.data[0] || null;
        const driverList = driverPayload.data || [];

        setSessionInfo(session);
        setDrivers(driverList);
        setPositions(getLatestPositions(positionPayload.data || []));
        setIntervals(getLatestIntervals(intervalPayload || []));
        setRaceControl(
          [...(raceControlPayload || [])]
            .sort((a, b) => +new Date(b.date) - +new Date(a.date))
            .slice(0, 8)
        );
        setFastestLap(fastestLapPayload || null);
        setSelectedDrivers((current) =>
          current.length > 0
            ? current.filter((driverNumber) =>
                driverList.some(
                  (driver) => driver.driver_number === driverNumber
                )
              )
            : driverList.slice(0, 4).map((driver) => driver.driver_number)
        );
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setPageError(
          error instanceof ApiError
            ? error.message
            : 'Failed to load telemetry session context.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadContext();

    return () => {
      isMounted = false;
    };
  }, [selectedSession]);

  useEffect(() => {
    if (livePositions.length > 0) {
      setPositions(getLatestPositions(livePositions));
    }
  }, [livePositions]);

  useEffect(() => {
    if (selectedSession && isConnected && selectedDrivers.length > 0) {
      subscribe({
        session_key: selectedSession,
        driver_numbers: selectedDrivers,
        channels: ['telemetry', 'positions', 'pit_stop', 'weather'],
      });
    }
  }, [selectedDrivers, selectedSession, isConnected, subscribe]);

  const selectedDriverCards = useMemo(
    () =>
      drivers.filter((driver) => selectedDrivers.includes(driver.driver_number)),
    [drivers, selectedDrivers]
  );

  const trackMapDrivers = useMemo<DriverInfo[]>(
    () =>
      drivers.map((driver) => {
        const name = getDriverNameParts(driver);
        return {
          driver_number: driver.driver_number,
          name_acronym: driver.name_acronym,
          first_name: name.firstName,
          last_name: name.lastName,
          team_name: driver.team_name,
          team_colour: driver.team_colour,
        };
      }),
    [drivers]
  );

  const trackMapPositions = useMemo<DriverPosition[]>(
    () =>
      positions.map((position) => {
        const latestTelemetry = telemetry.get(position.driver_number)?.at(-1);
        return {
          driver_number: position.driver_number,
          x: position.x ?? 500,
          y: position.y ?? 500,
          z: position.z,
          position: position.position,
          speed: latestTelemetry?.speed,
          drs: latestTelemetry?.drs,
          date: position.date,
        };
      }),
    [positions, telemetry]
  );

  const toggleDriver = (driverNumber: number) => {
    setSelectedDrivers((current) =>
      current.includes(driverNumber)
        ? current.filter((item) => item !== driverNumber)
        : [...current, driverNumber]
    );
  };

  return (
    <Layout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="OpenF1 Live"
          title="Telemetry Control Room"
          description="Dedicated live workspace for driver telemetry, position tracking, weather and race control messages. This page uses the current OpenF1 session plus the existing WebSocket stream."
          actions={
            <>
              <ConnectionStatus
                isConnected={isConnected}
                connectionState={connectionState}
                lastHeartbeat={lastHeartbeat}
                showDetails
              />
              {selectedSession ? (
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.2em] text-slate-300">
                  Session {selectedSession}
                </span>
              ) : null}
            </>
          }
        />

        <SimpleSessionSelector
          onSelect={(sessionKey) => {
            setSelectedSession(sessionKey);
            if (!isConnected) {
              connect();
            }
          }}
        />

        {!selectedSession ? (
          <EmptyState
            title="Select a session to start streaming telemetry"
            description="Choose a recent race weekend and session above. The page will load the live grid, latest positions, interval data, fastest lap snapshot and weather widget."
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
              </svg>
            }
          />
        ) : null}

        {pageError ? (
          <Surface className="border-red-500/30">
            <p className="text-sm text-red-300">{pageError}</p>
          </Surface>
        ) : null}

        {selectedSession ? (
          <>
            <div className="panel-grid">
              <StatCard
                label="Session"
                value={sessionInfo?.session_name || 'Live'}
                helper={
                  sessionInfo
                    ? `${sessionInfo.circuit_short_name} • ${sessionInfo.country_name}`
                    : 'Waiting for session metadata'
                }
                tone="accent"
              />
              <StatCard
                label="Drivers"
                value={drivers.length}
                helper="Grid resolved from OpenF1 driver data"
              />
              <StatCard
                label="Fastest Lap"
                value={
                  fastestLap?.lap_duration != null
                    ? `${fastestLap.lap_duration.toFixed(3)}s`
                    : 'Pending'
                }
                helper={
                  fastestLap?.driver_number && fastestLap?.lap_number
                    ? `Car #${fastestLap.driver_number} on lap ${fastestLap.lap_number}`
                    : 'Best lap snapshot for the selected session'
                }
                tone="warning"
              />
              <StatCard
                label="Race Control"
                value={raceControl.length}
                helper="Recent control messages available in the feed"
                tone="success"
              />
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
              <div className="space-y-6">
                <Surface
                  title="Selected Drivers"
                  subtitle="Toggle drivers to focus the live charts and map."
                >
                  <div className="grid gap-3 md:grid-cols-2">
                    {drivers.map((driver) => (
                      <SimpleDriverCard
                        key={driver.driver_number}
                        driver={driver}
                        isSelected={selectedDrivers.includes(driver.driver_number)}
                        onToggle={() => toggleDriver(driver.driver_number)}
                      />
                    ))}
                  </div>
                </Surface>

                <Surface
                  title="Telemetry Charts"
                  subtitle="Live chart stack for the currently selected drivers."
                >
                  <div className="grid gap-4 xl:grid-cols-2">
                    <TelemetryChart
                      title="Speed"
                      data={telemetry as Map<number, LiveTelemetryData[]>}
                      dataKey="speed"
                      selectedDrivers={selectedDrivers}
                      drivers={drivers}
                    />
                    <TelemetryChart
                      title="Throttle"
                      data={telemetry as Map<number, LiveTelemetryData[]>}
                      dataKey="throttle"
                      selectedDrivers={selectedDrivers}
                      drivers={drivers}
                    />
                    <TelemetryChart
                      title="RPM"
                      data={telemetry as Map<number, LiveTelemetryData[]>}
                      dataKey="rpm"
                      selectedDrivers={selectedDrivers}
                      drivers={drivers}
                    />
                    <TelemetryChart
                      title="Brake"
                      data={telemetry as Map<number, LiveTelemetryData[]>}
                      dataKey="brake"
                      selectedDrivers={selectedDrivers}
                      drivers={drivers}
                    />
                  </div>
                </Surface>
              </div>

              <div className="space-y-6">
                <Surface
                  title="Track Map"
                  subtitle="Live positions plotted with the existing track component."
                >
                  <TrackMap
                    circuitName={sessionInfo?.circuit_short_name}
                    positions={trackMapPositions}
                    drivers={trackMapDrivers}
                    selectedDrivers={selectedDrivers}
                    onDriverClick={toggleDriver}
                    size="md"
                  />
                </Surface>

                <Leaderboard
                  positions={positions}
                  drivers={drivers}
                  intervals={intervals}
                />

                <WeatherWidget
                  circuitName={sessionInfo?.circuit_short_name}
                  compact={false}
                />

                <Surface
                  title="Race Control"
                  subtitle="Most recent control messages returned by OpenF1."
                >
                  {raceControl.length === 0 ? (
                    <EmptyState
                      title="No recent race control messages"
                      description="When the selected session publishes flags, safety car events or other race control events, they will appear here."
                      icon={
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                        </svg>
                      }
                    />
                  ) : (
                    <div className="space-y-3">
                      {raceControl.map((message) => (
                        <div
                          key={`${message.date}-${message.message}-${message.driver_number || 'all'}`}
                          className="rounded-2xl border border-white/8 bg-white/[0.03] p-4"
                        >
                          <div className="flex items-center justify-between gap-4">
                            <div className="space-y-1">
                              <p className="font-medium text-white">
                                {message.message || 'Race control update'}
                              </p>
                              <p className="text-sm text-slate-400">
                                {[message.category, message.flag, message.scope]
                                  .filter(Boolean)
                                  .join(' • ') || 'General message'}
                              </p>
                            </div>
                            <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
                              {new Date(message.date).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Surface>
              </div>
            </div>
          </>
        ) : null}

        {isLoading ? (
          <Surface>
            <p className="text-sm text-slate-400">Loading telemetry workspace…</p>
          </Surface>
        ) : null}

        {selectedDriverCards.length === 0 && selectedSession && !isLoading ? (
          <EmptyState
            title="Choose at least one driver"
            description="The charts and telemetry stream only start rendering once at least one driver is selected."
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
              </svg>
            }
          />
        ) : null}
      </div>
    </Layout>
  );
}

function getLatestPositions(positions: LivePositionData[]): LivePositionData[] {
  const latest = new Map<number, LivePositionData>();
  [...positions]
    .sort((a, b) => +new Date(a.date) - +new Date(b.date))
    .forEach((position) => {
      latest.set(position.driver_number, position);
    });

  return Array.from(latest.values()).sort((a, b) => a.position - b.position);
}

function getLatestIntervals(intervals: IntervalData[]): IntervalData[] {
  const latest = new Map<number, IntervalData>();
  [...intervals]
    .sort((a, b) => +new Date(a.date) - +new Date(b.date))
    .forEach((interval) => {
      latest.set(interval.driver_number, interval);
    });
  return Array.from(latest.values());
}
