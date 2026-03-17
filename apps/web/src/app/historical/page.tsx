'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import Layout from '@/components/layout/Layout';
import PageHeader from '@/components/ui/PageHeader';
import { EmptyState, StatCard, Surface } from '@/components/ui/Surface';
import { apiFetch, ApiError } from '@/lib/api';
import type {
  FastF1DriverComparison,
  FastF1FastestLap,
  FastF1LapsResponse,
  FastF1SessionInfo,
  FastF1TelemetryResponse,
  FastF1WeatherResponse,
} from '@/types/fastf1';
import type { F1DbRace, ListResponse, PaginatedResponse } from '@/types/f1db';

const sessionOptions = ['R', 'Q', 'S', 'FP1', 'FP2', 'FP3'];

function getRaceRound(race: F1DbRace): number {
  return race.round_number ?? race.round;
}

function getRaceDate(race: F1DbRace): string {
  return race.race_date ?? race.date;
}

export default function HistoricalPage() {
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [seasonRaces, setSeasonRaces] = useState<F1DbRace[]>([]);
  const [selectedRound, setSelectedRound] = useState<number | null>(null);
  const [sessionType, setSessionType] = useState('R');
  const [sessionInfo, setSessionInfo] = useState<FastF1SessionInfo | null>(null);
  const [laps, setLaps] = useState<FastF1LapsResponse | null>(null);
  const [weather, setWeather] = useState<FastF1WeatherResponse | null>(null);
  const [fastestLap, setFastestLap] = useState<FastF1FastestLap | null>(null);
  const [comparison, setComparison] = useState<FastF1DriverComparison | null>(null);
  const [telemetry, setTelemetry] = useState<FastF1TelemetryResponse | null>(null);
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSeasons = async () => {
      try {
        const seasonPayload = await apiFetch<ListResponse<number>>('/api/f1db/seasons');
        setSeasons(seasonPayload.data);
        setSelectedSeason(
          seasonPayload.data.length > 0 ? Math.max(...seasonPayload.data) : 2024
        );
      } catch (fetchError) {
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load historical seasons.'
        );
      }
    };

    loadSeasons();
  }, []);

  useEffect(() => {
    if (!selectedSeason) {
      return;
    }

    const loadSeasonRaces = async () => {
      try {
        const racePayload = await apiFetch<PaginatedResponse<F1DbRace>>(
          `/api/f1db/seasons/${selectedSeason}/races`,
          {
            params: { page_size: 25 },
          }
        );
        setSeasonRaces(racePayload.data);
        setSelectedRound(racePayload.data[0] ? getRaceRound(racePayload.data[0]) : null);
      } catch (fetchError) {
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load season races.'
        );
      }
    };

    loadSeasonRaces();
  }, [selectedSeason]);

  useEffect(() => {
    if (!selectedSeason || !selectedRound) {
      return;
    }

    const loadHistoricalWorkspace = async () => {
      try {
        setError(null);
        const params = {
          year: selectedSeason,
          grand_prix: selectedRound,
          session_type: sessionType,
        };

        const sessionPayload = await apiFetch<FastF1SessionInfo>('/api/fastf1/session', {
          params,
        });

        setSessionInfo(sessionPayload);

        const drivers = sessionPayload.drivers || [];
        const primaryDriver = drivers[0] || null;
        setSelectedDriver(primaryDriver);

        const [lapsPayload, weatherPayload, fastestLapPayload] = await Promise.all([
          apiFetch<FastF1LapsResponse>('/api/fastf1/laps', { params }),
          apiFetch<FastF1WeatherResponse>('/api/fastf1/weather', { params }),
          apiFetch<FastF1FastestLap>('/api/fastf1/fastest-lap', { params }),
        ]);

        setLaps(lapsPayload);
        setWeather(weatherPayload);
        setFastestLap(fastestLapPayload);

        if (drivers.length >= 2) {
          const comparePayload = await apiFetch<FastF1DriverComparison>(
            '/api/fastf1/compare',
            {
              params: {
                ...params,
                drivers: drivers.slice(0, 2).join(','),
              },
            }
          );
          setComparison(comparePayload);
        } else {
          setComparison(null);
        }
      } catch (fetchError) {
        setSessionInfo(null);
        setLaps(null);
        setWeather(null);
        setFastestLap(null);
        setComparison(null);
        setTelemetry(null);
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load FastF1 session.'
        );
      }
    };

    loadHistoricalWorkspace();
  }, [selectedSeason, selectedRound, sessionType]);

  useEffect(() => {
    if (!selectedSeason || !selectedRound || !selectedDriver) {
      return;
    }

    const loadTelemetry = async () => {
      try {
        const telemetryPayload = await apiFetch<FastF1TelemetryResponse>(
          '/api/fastf1/telemetry',
          {
            params: {
              year: selectedSeason,
              grand_prix: selectedRound,
              session_type: sessionType,
              driver: selectedDriver,
            },
          }
        );
        setTelemetry(telemetryPayload);
      } catch (fetchError) {
        setTelemetry(null);
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load FastF1 telemetry.'
        );
      }
    };

    loadTelemetry();
  }, [selectedDriver, selectedRound, selectedSeason, sessionType]);

  const selectedRace =
    seasonRaces.find((race) => getRaceRound(race) === selectedRound) || null;

  const telemetryChartData = useMemo(
    () =>
      (telemetry?.data || []).slice(0, 400).map((sample) => ({
        time: sample.time,
        speed: sample.speed,
        throttle: sample.throttle,
        rpm: sample.rpm,
      })),
    [telemetry]
  );

  return (
    <Layout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="FastF1 Analysis"
          title="Historical Session Lab"
          description="FastF1-backed workspace for historical sessions. Use the F1DB season schedule as the selector, then inspect laps, weather, fastest lap and telemetry for a chosen driver."
          actions={
            <div className="flex flex-wrap gap-3">
              <label className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
                <span className="font-mono text-[11px] uppercase tracking-[0.24em] text-slate-500">
                  Season
                </span>
                <select
                  id="historical-season"
                  name="historical-season"
                  value={selectedSeason ?? ''}
                  onChange={(event) => setSelectedSeason(Number(event.target.value))}
                  className="bg-transparent text-white outline-none"
                >
                  {seasons.map((season) => (
                    <option key={season} value={season} className="bg-slate-950">
                      {season}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
                <span className="font-mono text-[11px] uppercase tracking-[0.24em] text-slate-500">
                  Session
                </span>
                <select
                  id="historical-session"
                  name="historical-session"
                  value={sessionType}
                  onChange={(event) => setSessionType(event.target.value)}
                  className="bg-transparent text-white outline-none"
                >
                  {sessionOptions.map((option) => (
                    <option key={option} value={option} className="bg-slate-950">
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          }
        />

        <div className="panel-grid">
          <StatCard
            label="Grand Prix"
            value={selectedRace?.grand_prix_id || 'Pending'}
            helper={selectedRace?.official_name || 'Pick a round below'}
            tone="accent"
          />
          <StatCard
            label="Drivers"
            value={sessionInfo?.drivers.length ?? 0}
            helper="Driver codes exposed by the selected FastF1 session"
          />
          <StatCard
            label="Total Laps"
            value={sessionInfo?.total_laps ?? 0}
            helper="Loaded from FastF1 session metadata"
            tone="warning"
          />
          <StatCard
            label="Fastest Lap"
            value={
              fastestLap?.lap_time_seconds != null
                ? `${fastestLap.lap_time_seconds.toFixed(3)}s`
                : 'Pending'
            }
            helper={fastestLap?.driver || 'Session benchmark'}
            tone="success"
          />
        </div>

        {error ? (
          <Surface className="border-red-500/30">
            <p className="text-sm text-red-300">{error}</p>
          </Surface>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-6">
            <Surface
              title="Season Schedule"
              subtitle="Use the season rounds from F1DB to choose the historical event."
            >
              {seasonRaces.length === 0 ? (
                <EmptyState
                  title="No races available"
                  description="The local F1DB snapshot may not have season rounds for this year."
                />
              ) : (
                <div className="grid gap-3">
                  {seasonRaces.map((race) => (
                    <button
                      key={race.id}
                      onClick={() => setSelectedRound(getRaceRound(race))}
                      className={`rounded-[20px] border p-4 text-left transition-colors ${
                        selectedRound === getRaceRound(race)
                          ? 'border-f1-red bg-f1-red/10'
                          : 'border-white/8 bg-white/[0.03] hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium text-white">{race.official_name}</p>
                          <p className="mt-1 text-sm text-slate-400">
                            Round {getRaceRound(race)} •{' '}
                            {new Date(getRaceDate(race)).toLocaleDateString()}
                          </p>
                        </div>
                        <span className="rounded-full border border-white/10 px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.2em] text-slate-300">
                          {race.qualifying_format}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </Surface>

            <Surface
              title="Fastest Lap + Comparison"
              subtitle="Session benchmark and two-driver delta from FastF1."
            >
              {fastestLap ? (
                <div className="space-y-4">
                  <div className="rounded-[20px] border border-white/8 bg-white/[0.03] p-4">
                    <p className="font-medium text-white">{fastestLap.driver}</p>
                    <p className="mt-1 text-2xl font-semibold text-white">
                      {fastestLap.lap_time || 'N/A'}
                    </p>
                    <p className="mt-2 text-sm text-slate-400">
                      Lap {fastestLap.lap_number} • {fastestLap.tyre_compound || 'Unknown tyre'}
                    </p>
                  </div>
                  {comparison ? (
                    <div className="space-y-3">
                      {Object.entries(comparison.telemetry_delta).map(
                        ([label, delta]) => (
                          <div
                            key={label}
                            className="rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3"
                          >
                            <p className="font-medium text-white">{label}</p>
                            <p className="mt-1 text-sm text-slate-400">
                              Delta {delta.delta.toFixed(3)}s • Faster:{' '}
                              <span className="text-white">{delta.faster}</span>
                            </p>
                          </div>
                        )
                      )}
                    </div>
                  ) : null}
                </div>
              ) : (
                <EmptyState
                  title="Fastest lap pending"
                  description="Load a session to inspect the benchmark lap and the comparison delta."
                />
              )}
            </Surface>
          </div>

          <div className="space-y-6">
            <Surface
              title="Telemetry Trace"
              subtitle="Single-driver speed, throttle and RPM trace from FastF1."
              actions={
                sessionInfo?.drivers.length ? (
                  <select
                    id="historical-driver"
                    name="historical-driver"
                    value={selectedDriver ?? ''}
                    onChange={(event) => setSelectedDriver(event.target.value)}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none"
                  >
                    {sessionInfo.drivers.map((driver) => (
                      <option key={driver} value={driver} className="bg-slate-950">
                        {driver}
                      </option>
                    ))}
                  </select>
                ) : null
              }
            >
              {telemetryChartData.length === 0 ? (
                <EmptyState
                  title="Telemetry not loaded"
                  description="Pick a driver once the session has loaded to render the historical trace."
                />
              ) : (
                <div className="h-[340px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={telemetryChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="time" stroke="#94a3b8" tick={false} />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#020617',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '12px',
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="speed"
                        stroke="#E80020"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="throttle"
                        stroke="#22c55e"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="rpm"
                        stroke="#38bdf8"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Surface>

            <Surface
              title="Weather Summary"
              subtitle="Aggregated session weather statistics from FastF1."
            >
              {!weather?.summary ? (
                <EmptyState
                  title="Weather summary unavailable"
                  description="The selected session may not expose enough weather data in the FastF1 cache."
                />
              ) : (
                <div className="grid gap-3 sm:grid-cols-2">
                  <StatCard
                    label="Air Temp"
                    value={`${weather.summary.air_temp?.avg?.toFixed(1) ?? '0.0'}°C`}
                    helper="Average session air temperature"
                    tone="accent"
                  />
                  <StatCard
                    label="Track Temp"
                    value={`${weather.summary.track_temp?.avg?.toFixed(1) ?? '0.0'}°C`}
                    helper="Average track temperature"
                    tone="warning"
                  />
                  <StatCard
                    label="Humidity"
                    value={`${weather.summary.humidity?.avg?.toFixed(0) ?? '0'}%`}
                    helper="Average humidity"
                  />
                  <StatCard
                    label="Rainfall"
                    value={weather.summary.rainfall ? 'Yes' : 'No'}
                    helper="Rain detected during session"
                    tone="success"
                  />
                </div>
              )}
            </Surface>

            <Surface
              title="Lap Table"
              subtitle="Latest laps from the selected historical session."
            >
              {!laps?.laps.length ? (
                <EmptyState
                  title="No laps available"
                  description="When FastF1 loads the chosen session, the lap table will appear here."
                />
              ) : (
                <div className="space-y-3">
                  {laps.laps.slice(0, 10).map((lap) => (
                    <div
                      key={`${lap.driver}-${lap.lap_number}`}
                      className="flex items-center justify-between rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3"
                    >
                      <div>
                        <p className="font-medium text-white">
                          {lap.driver} • Lap {lap.lap_number}
                        </p>
                        <p className="mt-1 text-sm text-slate-400">
                          {lap.tyre_compound || 'Unknown tyre'} •{' '}
                          {lap.tyre_life != null ? `${lap.tyre_life} laps old` : 'Tyre life N/A'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-white">
                          {lap.lap_time != null ? `${lap.lap_time.toFixed(3)}s` : 'N/A'}
                        </p>
                        <p className="text-sm text-slate-400">
                          Sectors {lap.sector_1?.toFixed(2) ?? '--'} /{' '}
                          {lap.sector_2?.toFixed(2) ?? '--'} /{' '}
                          {lap.sector_3?.toFixed(2) ?? '--'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Surface>
          </div>
        </div>
      </div>
    </Layout>
  );
}
