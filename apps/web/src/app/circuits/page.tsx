'use client';

import { useEffect, useMemo, useState } from 'react';
import Layout from '@/components/layout/Layout';
import WeatherWidget from '@/components/dashboard/WeatherWidget';
import PageHeader from '@/components/ui/PageHeader';
import { EmptyState, StatCard, Surface } from '@/components/ui/Surface';
import { apiFetch, ApiError } from '@/lib/api';
import type { F1DbCircuit, F1DbRace, PaginatedResponse } from '@/types/f1db';

function getRaceRound(race: F1DbRace): number {
  return race.round_number ?? race.round;
}

function getRaceDate(race: F1DbRace): string {
  return race.race_date ?? race.date;
}

export default function CircuitsPage() {
  const [circuits, setCircuits] = useState<F1DbCircuit[]>([]);
  const [selectedCircuitId, setSelectedCircuitId] = useState<string | null>(null);
  const [selectedCircuit, setSelectedCircuit] = useState<F1DbCircuit | null>(null);
  const [recentRaces, setRecentRaces] = useState<F1DbRace[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCircuits = async () => {
      try {
        const payload = await apiFetch<PaginatedResponse<F1DbCircuit>>(
          '/api/f1db/circuits',
          {
            params: { page_size: 100 },
          }
        );
        setCircuits(payload.data);
        setSelectedCircuitId(payload.data[0]?.id || null);
      } catch (fetchError) {
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load circuit catalog.'
        );
      }
    };

    loadCircuits();
  }, []);

  useEffect(() => {
    if (!selectedCircuitId) {
      return;
    }

    const loadCircuit = async () => {
      try {
        setError(null);
        const [circuit, racesPayload] = await Promise.all([
          apiFetch<F1DbCircuit>(`/api/f1db/circuits/${selectedCircuitId}`),
          apiFetch<PaginatedResponse<F1DbRace>>('/api/f1db/races', {
            params: { circuit_id: selectedCircuitId, page_size: 8 },
          }),
        ]);
        setSelectedCircuit(circuit);
        setRecentRaces(racesPayload.data);
      } catch (fetchError) {
        setSelectedCircuit(null);
        setRecentRaces([]);
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load circuit details.'
        );
      }
    };

    loadCircuit();
  }, [selectedCircuitId]);

  const filteredCircuits = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    if (!normalizedSearch) {
      return circuits;
    }

    return circuits.filter((circuit) =>
      [circuit.name, circuit.full_name, circuit.place_name, circuit.country_id]
        .join(' ')
        .toLowerCase()
        .includes(normalizedSearch)
    );
  }, [circuits, searchTerm]);

  return (
    <Layout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="F1DB + Weather"
          title="Circuit Atlas"
          description="Track directory powered by F1DB, with recent race history and live weather lookups from the existing weather integration."
          actions={
            <input
              id="circuits-search"
              name="circuits-search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search circuit"
              className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white outline-none placeholder:text-slate-500"
            />
          }
        />

        <div className="panel-grid">
          <StatCard
            label="Circuits"
            value={circuits.length}
            helper="Entries available in the local F1DB snapshot"
            tone="accent"
          />
          <StatCard
            label="Selected"
            value={selectedCircuit?.name || 'None'}
            helper={selectedCircuit?.country_id || 'Pick a circuit from the list'}
          />
          <StatCard
            label="Turns"
            value={selectedCircuit?.turns ?? 0}
            helper="Track layout complexity"
            tone="warning"
          />
          <StatCard
            label="Races Held"
            value={selectedCircuit?.total_races_held ?? 0}
            helper="Total grands prix hosted at this venue"
            tone="success"
          />
        </div>

        {error ? (
          <Surface className="border-red-500/30">
            <p className="text-sm text-red-300">{error}</p>
          </Surface>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <Surface
            title="Circuit Directory"
            subtitle="Pick a circuit to inspect metadata, weather and recent races."
          >
            {filteredCircuits.length === 0 ? (
              <EmptyState
                title="No circuits matched the current search"
                description="Try a broader term or clear the search box."
              />
            ) : (
              <div className="grid gap-3">
                {filteredCircuits.map((circuit) => (
                  <button
                    key={circuit.id}
                    onClick={() => setSelectedCircuitId(circuit.id)}
                    className={`rounded-[22px] border p-4 text-left transition-colors ${
                      selectedCircuitId === circuit.id
                        ? 'border-f1-red bg-f1-red/10'
                        : 'border-white/8 bg-white/[0.03] hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-white">{circuit.full_name}</p>
                        <p className="mt-1 text-sm text-slate-400">
                          {circuit.place_name} • {circuit.country_id}
                        </p>
                      </div>
                      <span className="rounded-full border border-white/10 px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.2em] text-slate-300">
                        {circuit.type}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-400">
                      <span>{circuit.length.toFixed(3)} km</span>
                      <span>{circuit.turns} turns</span>
                      <span>{circuit.direction.replace('_', ' ')}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Surface>

          <div className="space-y-6">
            <Surface
              title="Circuit Profile"
              subtitle="Core metadata and coordinates from F1DB."
            >
              {!selectedCircuit ? (
                <EmptyState
                  title="Select a circuit"
                  description="The profile panel updates with the venue, length, direction, location and recent races."
                />
              ) : (
                <div className="space-y-5">
                  <div>
                    <p className="font-display text-3xl uppercase tracking-[0.04em] text-white">
                      {selectedCircuit.name}
                    </p>
                    <p className="mt-2 text-sm text-slate-400">
                      {selectedCircuit.full_name}
                    </p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <StatCard
                      label="Length"
                      value={`${selectedCircuit.length.toFixed(3)} km`}
                      helper="Official course length"
                      tone="accent"
                    />
                    <StatCard
                      label="Direction"
                      value={selectedCircuit.direction.replace('_', ' ')}
                      helper="Track running direction"
                    />
                    <StatCard
                      label="Place"
                      value={selectedCircuit.place_name}
                      helper={selectedCircuit.country_id}
                      tone="warning"
                    />
                    <StatCard
                      label="Coordinates"
                      value={`${selectedCircuit.latitude.toFixed(2)}, ${selectedCircuit.longitude.toFixed(2)}`}
                      helper="Lat / Lon"
                      tone="success"
                    />
                  </div>
                </div>
              )}
            </Surface>

            {selectedCircuit ? (
              <WeatherWidget
                latitude={selectedCircuit.latitude}
                longitude={selectedCircuit.longitude}
              />
            ) : null}

            <Surface
              title="Recent Race History"
              subtitle="Latest races recorded at this venue inside F1DB."
            >
              {recentRaces.length === 0 ? (
                <EmptyState
                  title="No race history found"
                  description="The local database may not include race entries for this circuit yet."
                />
              ) : (
                <div className="space-y-3">
                  {recentRaces.map((race) => (
                    <div
                      key={race.id}
                      className="rounded-[20px] border border-white/8 bg-white/[0.03] px-4 py-3"
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-medium text-white">{race.official_name}</p>
                          <p className="mt-1 text-sm text-slate-400">
                            Round {getRaceRound(race)} •{' '}
                            {new Date(getRaceDate(race)).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="text-right text-sm text-slate-400">
                          <p>{race.laps} laps</p>
                          <p>{race.distance.toFixed(1)} km</p>
                        </div>
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
