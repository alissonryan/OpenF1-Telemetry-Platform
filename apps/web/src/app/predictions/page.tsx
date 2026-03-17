'use client';

import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SimpleSessionSelector from '@/components/dashboard/SimpleSessionSelector';
import PitStopPredictionCard from '@/components/predictions/PitStopPredictionCard';
import PositionForecastTable from '@/components/predictions/PositionForecastTable';
import StrategyRecommendations from '@/components/predictions/StrategyRecommendations';
import ConnectionStatus from '@/components/ui/ConnectionStatus';
import PageHeader from '@/components/ui/PageHeader';
import { EmptyState, StatCard, Surface, Badge } from '@/components/ui/Surface';
import { usePredictions } from '@/hooks/usePredictions';
import { apiFetch, ApiError } from '@/lib/api';
import { getDriverDisplayName } from '@/lib/driver';
import type {
  DriverPositionForecast,
  PitPrediction,
  StrategyAnalysis,
} from '@/types/predictions';
import type { Driver } from '@/types/telemetry';

interface ModelStatusPayload {
  pit_predictor: Record<string, unknown>;
  position_forecaster: Record<string, unknown>;
  strategy_recommender: Record<string, unknown>;
  models_loaded: boolean;
  overall_mode?: string;
}

const tabs = [
  { id: 'pit' as const, label: 'Pit Window', icon: 'Pit' },
  { id: 'positions' as const, label: 'Position Drift', icon: 'Pos' },
  { id: 'strategy' as const, label: 'Strategy', icon: 'Str' },
];

const getBadgeTone = (mode: string) => {
  if (mode === 'trained_model') return 'success';
  if (mode === 'heuristic_fallback') return 'warning';
  if (mode === 'rule_based') return 'info';
  return 'default';
};

export default function PredictionsPage() {
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  const [activeTab, setActiveTab] =
    useState<'pit' | 'positions' | 'strategy'>('pit');
  const [modelStatus, setModelStatus] = useState<ModelStatusPayload | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);

  const {
    pitPredictions,
    positionForecast,
    strategies,
    isLoadingPit,
    isLoadingPositions,
    isLoadingStrategy,
    pitError,
    positionError,
    strategyError,
    lastUpdate,
    isConnected,
  } = usePredictions({
    sessionKey: selectedSession || undefined,
    autoRefresh: true,
    refreshInterval: 10000,
  });

  useEffect(() => {
    const loadModelStatus = async () => {
      try {
        const payload = await apiFetch<ModelStatusPayload>(
          '/api/predictions/models/status'
        );
        setModelStatus(payload);
      } catch (fetchError) {
        setPageError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load prediction mode.'
        );
      }
    };

    loadModelStatus();
  }, []);

  useEffect(() => {
    if (!selectedSession) {
      return;
    }

    const loadDrivers = async () => {
      try {
        const payload = await apiFetch<{ data: Driver[] }>('/api/telemetry/drivers', {
          params: { session_key: selectedSession },
        });
        setDrivers(payload.data);
        setSelectedDrivers(
          payload.data.slice(0, 6).map((driver) => driver.driver_number)
        );
      } catch (fetchError) {
        setDrivers([]);
        setPageError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load selected session drivers.'
        );
      }
    };

    loadDrivers();
  }, [selectedSession]);

  const selectedPitPredictions = useMemo(() => {
    const predictions: Array<{ driver: Driver; prediction: PitPrediction }> = [];

    selectedDrivers.forEach((driverNumber) => {
      const prediction = pitPredictions.get(driverNumber);
      const driver = drivers.find((item) => item.driver_number === driverNumber);

      if (prediction && driver) {
        predictions.push({ driver, prediction });
      }
    });

    return predictions.sort(
      (left, right) => right.prediction.probability - left.prediction.probability
    );
  }, [drivers, pitPredictions, selectedDrivers]);

  const selectedStrategies = useMemo(() => {
    const strategyList: StrategyAnalysis[] = [];

    selectedDrivers.forEach((driverNumber) => {
      const strategy = strategies.get(driverNumber);
      if (strategy) {
        strategyList.push(strategy);
      }
    });

    return strategyList;
  }, [selectedDrivers, strategies]);

  const filteredPositionForecast = useMemo(() => {
    const enriched = positionForecast.map((prediction: DriverPositionForecast) => {
      const driver = drivers.find(
        (item) => item.driver_number === prediction.driver_number
      );
      return {
        ...prediction,
        driver_name: driver
          ? getDriverDisplayName(driver)
          : `Driver ${prediction.driver_number}`,
        team_name: driver?.team_name || prediction.team_name || 'Unknown',
      };
    });

    return selectedDrivers.length > 0
      ? enriched.filter((prediction) =>
          selectedDrivers.includes(prediction.driver_number)
        )
      : enriched;
  }, [drivers, positionForecast, selectedDrivers]);

  const topPrediction = selectedPitPredictions[0];

  return (
    <Layout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Hybrid Prediction Layer"
          title="Predictions Workspace"
          description="This page combines live session context with whichever prediction assets are currently available. If trained models are missing, the pit and position outputs fall back to heuristics; strategy remains rule-based by design."
          actions={
            <div className="flex flex-wrap items-center gap-3">
              <ConnectionStatus
                isConnected={isConnected}
                connectionState={isConnected ? 'connected' : 'disconnected'}
                showDetails={false}
              />
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.2em] text-slate-300">
                {modelStatus?.overall_mode || 'unknown'}
              </span>
            </div>
          }
        />

        <SimpleSessionSelector onSelect={setSelectedSession} />

        <div className="panel-grid">
          <StatCard
            label="Mode"
            value={
              <Badge tone={getBadgeTone(modelStatus?.overall_mode || '')}>
                {modelStatus?.overall_mode || 'Unknown'}
              </Badge>
            }
            helper="Overall prediction runtime mode"
            tone="accent"
          />
          <StatCard
            label="Pit Engine"
            value={
              <Badge tone={getBadgeTone(String(modelStatus?.pit_predictor?.mode || ''))}>
                {String(modelStatus?.pit_predictor?.mode || 'unknown')}
              </Badge>
            }
            helper="Trained model or heuristic fallback"
          />
          <StatCard
            label="Position Engine"
            value={
              <Badge tone={getBadgeTone(String(modelStatus?.position_forecaster?.mode || ''))}>
                {String(modelStatus?.position_forecaster?.mode || 'unknown')}
              </Badge>
            }
            helper="Trained model or heuristic fallback"
            tone="warning"
          />
          <StatCard
            label="Top Pit Risk"
            value={
              topPrediction
                ? `${(topPrediction.prediction.probability * 100).toFixed(0)}%`
                : 'N/A'
            }
            helper={
              topPrediction
                ? `${topPrediction.driver.name_acronym} currently leads the pit-risk list`
                : 'Load a session to generate a live ranking'
            }
            tone="success"
          />
        </div>

        {pageError ? (
          <Surface className="border-red-500/30">
            <p className="text-sm text-red-300">{pageError}</p>
          </Surface>
        ) : null}

        {!selectedSession ? (
          <EmptyState
            title="Select a session to start generating predictions"
            description="Once a live session is selected, the page resolves the current driver roster, computes the live context and starts polling plus WebSocket updates for prediction bundles."
            icon={
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
          />
        ) : null}

        {selectedSession ? (
          <>
            <Surface
              title="Driver Focus"
              subtitle="Select which drivers should stay in focus across pit, position and strategy views."
              actions={
                lastUpdate ? (
                  <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
                    Updated {new Date(lastUpdate).toLocaleTimeString()}
                  </span>
                ) : null
              }
            >
              <div className="flex flex-wrap gap-2">
                {drivers.map((driver) => (
                  <button
                    key={driver.driver_number}
                    onClick={() =>
                      setSelectedDrivers((current) =>
                        current.includes(driver.driver_number)
                          ? current.filter((item) => item !== driver.driver_number)
                          : [...current, driver.driver_number]
                      )
                    }
                    className={`rounded-full border px-3 py-2 text-sm font-medium transition-colors ${
                      selectedDrivers.includes(driver.driver_number)
                        ? 'border-f1-red bg-f1-red text-white'
                        : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20'
                    }`}
                  >
                    {driver.name_acronym}
                  </button>
                ))}
              </div>
            </Surface>

            <Surface
              title="Prediction Views"
              subtitle="Switch between imminent pit windows, position drift and tyre strategy."
            >
              <div className="mb-5 flex flex-wrap gap-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-f1-red text-white'
                        : 'border border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20'
                    }`}
                  >
                    <span className="mr-2 font-mono text-xs uppercase tracking-[0.2em]">
                      {tab.icon}
                    </span>
                    {tab.label}
                  </button>
                ))}
              </div>

              <AnimatePresence mode="wait">
                {activeTab === 'pit' ? (
                  <motion.div
                    key="pit"
                    initial={{ opacity: 0, x: -18 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 18 }}
                    className="space-y-5"
                  >
                    {pitError ? (
                      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                        {pitError}
                      </div>
                    ) : null}

                    {selectedPitPredictions.length === 0 && !isLoadingPit ? (
                      <EmptyState
                        title="No pit predictions yet"
                        description="Keep at least one driver selected. The pit list fills as soon as the live prediction context resolves."
                        icon={
                          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        }
                      />
                    ) : (
                      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                        {selectedPitPredictions.map(({ driver, prediction }) => (
                          <PitStopPredictionCard
                            key={driver.driver_number}
                            driver={driver}
                            prediction={prediction}
                            isHighlighted={prediction.probability >= 0.7}
                          />
                        ))}
                      </div>
                    )}
                  </motion.div>
                ) : null}

                {activeTab === 'positions' ? (
                  <motion.div
                    key="positions"
                    initial={{ opacity: 0, x: -18 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 18 }}
                    className="space-y-5"
                  >
                    {positionError ? (
                      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                        {positionError}
                      </div>
                    ) : null}
                    <PositionForecastTable
                      predictions={filteredPositionForecast}
                      isLoading={isLoadingPositions}
                    />
                  </motion.div>
                ) : null}

                {activeTab === 'strategy' ? (
                  <motion.div
                    key="strategy"
                    initial={{ opacity: 0, x: -18 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 18 }}
                    className="space-y-5"
                  >
                    {strategyError ? (
                      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                        {strategyError}
                      </div>
                    ) : null}
                    <StrategyRecommendations
                      recommendations={selectedStrategies}
                      isLoading={isLoadingStrategy}
                    />
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </Surface>

            <Surface
              title="What you are seeing"
              subtitle="Short explanation for non-specialist users."
            >
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-[20px] border border-white/8 bg-white/[0.03] p-4">
                  <p className="font-medium text-white">Pit window</p>
                  <p className="mt-2 text-sm leading-6 text-slate-400">
                    Estimates who looks close to stopping soon based on tyre age,
                    pace drop, gap and stint shape.
                  </p>
                </div>
                <div className="rounded-[20px] border border-white/8 bg-white/[0.03] p-4">
                  <p className="font-medium text-white">Position drift</p>
                  <p className="mt-2 text-sm leading-6 text-slate-400">
                    Projects how the order may move over the next laps from the
                    current race snapshot.
                  </p>
                </div>
                <div className="rounded-[20px] border border-white/8 bg-white/[0.03] p-4">
                  <p className="font-medium text-white">Strategy advice</p>
                  <p className="mt-2 text-sm leading-6 text-slate-400">
                    Suggests conservative or aggressive pit windows and tyre mixes
                    based on the current stint.
                  </p>
                </div>
              </div>
            </Surface>
          </>
        ) : null}
      </div>
    </Layout>
  );
}
