'use client';

import { useEffect, useMemo, useState } from 'react';
import Layout from '@/components/layout/Layout';
import SimpleDriverCard from '@/components/dashboard/SimpleDriverCard';
import SimpleSessionSelector from '@/components/dashboard/SimpleSessionSelector';
import PageHeader from '@/components/ui/PageHeader';
import { EmptyState, StatCard, Surface } from '@/components/ui/Surface';
import { apiFetch, ApiError } from '@/lib/api';
import type {
  F1DbDriver,
  F1DbDriverStanding,
  F1DbDriverStatistics,
  PaginatedResponse,
  ListResponse,
} from '@/types/f1db';
import type { Driver } from '@/types/telemetry';

export default function DriversPage() {
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [drivers, setDrivers] = useState<F1DbDriver[]>([]);
  const [standings, setStandings] = useState<F1DbDriverStanding[]>([]);
  const [selectedDriverId, setSelectedDriverId] = useState<string | null>(null);
  const [selectedDriverStats, setSelectedDriverStats] =
    useState<F1DbDriverStatistics | null>(null);
  const [liveSessionDrivers, setLiveSessionDrivers] = useState<Driver[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
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
            : 'Failed to load F1DB seasons.'
        );
      }
    };

    loadSeasons();
  }, []);

  useEffect(() => {
    if (!selectedSeason) {
      return;
    }

    const loadSeasonDrivers = async () => {
      try {
        setError(null);
        const [driverPayload, standingsPayload] = await Promise.all([
          apiFetch<PaginatedResponse<F1DbDriver>>('/api/f1db/drivers', {
            params: { season: selectedSeason, page_size: 50 },
          }),
          apiFetch<ListResponse<F1DbDriverStanding>>(
            `/api/f1db/seasons/${selectedSeason}/standings/drivers`
          ),
        ]);

        setDrivers(driverPayload.data);
        setStandings(standingsPayload.data);
        setSelectedDriverId((current) =>
          current && driverPayload.data.some((driver) => driver.id === current)
            ? current
            : driverPayload.data[0]?.id || null
        );
      } catch (fetchError) {
        setDrivers([]);
        setStandings([]);
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load driver catalog.'
        );
      }
    };

    loadSeasonDrivers();
  }, [selectedSeason]);

  useEffect(() => {
    if (!selectedDriverId) {
      return;
    }

    const loadDriverStats = async () => {
      try {
        const stats = await apiFetch<F1DbDriverStatistics>(
          `/api/f1db/drivers/${selectedDriverId}/statistics`
        );
        setSelectedDriverStats(stats);
      } catch (fetchError) {
        setSelectedDriverStats(null);
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load driver statistics.'
        );
      }
    };

    loadDriverStats();
  }, [selectedDriverId]);

  const filteredDrivers = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    if (!normalizedSearch) {
      return drivers;
    }

    return drivers.filter((driver) =>
      [driver.full_name, driver.abbreviation, driver.country_of_birth_id]
        .join(' ')
        .toLowerCase()
        .includes(normalizedSearch)
    );
  }, [drivers, searchTerm]);

  const selectedDriver =
    drivers.find((driver) => driver.id === selectedDriverId) || null;

  return (
    <Layout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="F1DB + OpenF1"
          title="Drivers Archive"
          description="Season driver directory powered by F1DB, with a live roster sidecar from the currently selected OpenF1 session."
          actions={
            <div className="flex flex-wrap gap-3">
              <label className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
                <span className="font-mono text-[11px] uppercase tracking-[0.24em] text-slate-500">
                  Season
                </span>
                <select
                  id="drivers-season"
                  name="drivers-season"
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
              <input
                id="drivers-search"
                name="drivers-search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search driver"
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white outline-none placeholder:text-slate-500"
              />
            </div>
          }
        />

        <div className="panel-grid">
          <StatCard
            label="Season Drivers"
            value={drivers.length}
            helper={`Entries participating in ${selectedSeason ?? 'selected'} season`}
            tone="accent"
          />
          <StatCard
            label="Championship Leader"
            value={standings[0]?.driver_id || 'Pending'}
            helper="Final standings from F1DB"
          />
          <StatCard
            label="Live Grid"
            value={liveSessionDrivers.length}
            helper="Drivers resolved from the live session selector"
            tone="success"
          />
          <StatCard
            label="Selected Driver"
            value={selectedDriver?.abbreviation || 'None'}
            helper={selectedDriver ? selectedDriver.full_name : 'Pick a driver to inspect'}
            tone="warning"
          />
        </div>

        {error ? (
          <Surface className="border-red-500/30">
            <p className="text-sm text-red-300">{error}</p>
          </Surface>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <Surface
              title="Driver Directory"
              subtitle="Season-filtered driver catalog from F1DB."
            >
              {filteredDrivers.length === 0 ? (
                <EmptyState
                  title="No drivers matched the current filter"
                  description="Try a different season or clear the search query."
                />
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {filteredDrivers.map((driver) => (
                    <button
                      key={driver.id}
                      onClick={() => setSelectedDriverId(driver.id)}
                      className="text-left"
                    >
                      <div
                        className={`rounded-[20px] border p-4 transition-colors ${
                          selectedDriverId === driver.id
                            ? 'border-f1-red bg-f1-red/10'
                            : 'border-white/8 bg-white/[0.03] hover:border-white/20'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-white">{driver.full_name}</p>
                            <p className="mt-1 text-sm text-slate-400">
                              {driver.abbreviation}
                              {driver.permanent_number
                                ? ` • #${driver.permanent_number}`
                                : ''}
                            </p>
                          </div>
                          <span className="rounded-full border border-white/10 px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.2em] text-slate-300">
                            {driver.nationality_country_id}
                          </span>
                        </div>
                        <p className="mt-3 text-sm text-slate-400">
                          Born in {driver.place_of_birth} on{' '}
                          {new Date(driver.date_of_birth).toLocaleDateString()}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </Surface>

            <Surface
              title="Live Session Roster"
              subtitle="Resolve the current session grid and compare it with the historical archive."
            >
              <div className="space-y-4">
                <SimpleSessionSelector
                  onSelect={async (sessionKey) => {
                    try {
                      const payload = await apiFetch<{ data: Driver[] }>(
                        '/api/telemetry/drivers',
                        { params: { session_key: sessionKey } }
                      );
                      setLiveSessionDrivers(payload.data);
                    } catch (fetchError) {
                      setError(
                        fetchError instanceof ApiError
                          ? fetchError.message
                          : 'Failed to resolve live session roster.'
                      );
                    }
                  }}
                />
                {liveSessionDrivers.length === 0 ? (
                  <EmptyState
                    title="No live roster loaded yet"
                    description="Choose a recent session above to pull the current driver lineup from OpenF1."
                  />
                ) : (
                  <div className="grid gap-3 md:grid-cols-2">
                    {liveSessionDrivers.map((driver) => (
                      <SimpleDriverCard key={driver.driver_number} driver={driver} />
                    ))}
                  </div>
                )}
              </div>
            </Surface>
          </div>

          <div className="space-y-6">
            <Surface
              title="Driver Profile"
              subtitle="Selected driver biography and career totals."
            >
              {!selectedDriver ? (
                <EmptyState
                  title="Select a driver"
                  description="The right-side profile updates with driver statistics, titles, wins and points."
                />
              ) : (
                <div className="space-y-5">
                  <div>
                    <p className="font-display text-3xl uppercase tracking-[0.04em] text-white">
                      {selectedDriver.full_name}
                    </p>
                    <p className="mt-2 text-sm text-slate-400">
                      {selectedDriver.place_of_birth} •{' '}
                      {selectedDriver.nationality_country_id}
                    </p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <StatCard
                      label="Titles"
                      value={selectedDriverStats?.total_championship_wins ?? 0}
                      helper="World championships"
                      tone="accent"
                    />
                    <StatCard
                      label="Wins"
                      value={selectedDriverStats?.total_race_wins ?? 0}
                      helper="Career race victories"
                      tone="success"
                    />
                    <StatCard
                      label="Podiums"
                      value={selectedDriverStats?.total_podiums ?? 0}
                      helper="Career podium finishes"
                    />
                    <StatCard
                      label="Points"
                      value={selectedDriverStats?.total_points?.toFixed(1) ?? '0.0'}
                      helper="Total career points"
                      tone="warning"
                    />
                  </div>

                  <div className="rounded-[20px] border border-white/8 bg-white/[0.03] p-4">
                    <p className="font-medium text-white">Career snapshot</p>
                    <div className="mt-3 grid gap-3 text-sm text-slate-300">
                      <p>
                        Best championship finish:{' '}
                        <span className="text-white">
                          {selectedDriverStats?.best_championship_position ?? 'N/A'}
                        </span>
                      </p>
                      <p>
                        Pole positions:{' '}
                        <span className="text-white">
                          {selectedDriverStats?.total_pole_positions ?? 0}
                        </span>
                      </p>
                      <p>
                        Fastest laps:{' '}
                        <span className="text-white">
                          {selectedDriverStats?.total_fastest_laps ?? 0}
                        </span>
                      </p>
                      <p>
                        Grand slams:{' '}
                        <span className="text-white">
                          {selectedDriverStats?.total_grand_slams ?? 0}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </Surface>

            <Surface
              title="Season Standings"
              subtitle="Final championship table from the selected season."
            >
              {standings.length === 0 ? (
                <EmptyState
                  title="No standings available"
                  description="This season may not have final standings in the local F1DB snapshot yet."
                />
              ) : (
                <div className="space-y-3">
                  {standings.slice(0, 10).map((entry) => (
                    <div
                      key={entry.driver_id}
                      className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3"
                    >
                      <div>
                        <p className="font-medium text-white">{entry.driver_id}</p>
                        <p className="text-sm text-slate-400">
                          Position {entry.position_number ?? entry.position_text}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-sm uppercase tracking-[0.2em] text-slate-500">
                          Points
                        </p>
                        <p className="text-lg font-semibold text-white">
                          {entry.points}
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
