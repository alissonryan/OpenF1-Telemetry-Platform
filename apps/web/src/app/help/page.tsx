'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/layout/Layout';
import PageHeader from '@/components/ui/PageHeader';
import { EmptyState, StatCard, Surface, Badge } from '@/components/ui/Surface';
import { apiFetch, ApiError } from '@/lib/api';

interface ModelStatusPayload {
  pit_predictor: Record<string, unknown>;
  position_forecaster: Record<string, unknown>;
  strategy_recommender: Record<string, unknown>;
  models_loaded: boolean;
  overall_mode?: string;
}

const integrations = [
  {
    name: 'OpenF1',
    description:
      'Live meetings, sessions, drivers, positions, laps, pit stops, race control and radio.',
  },
  {
    name: 'FastF1',
    description:
      'Historical session load, detailed telemetry, weather and driver comparison workflows.',
  },
  {
    name: 'F1DB',
    description:
      'Long-range historical archive for drivers, circuits, races and season standings.',
  },
  {
    name: 'Open-Meteo',
    description:
      'Circuit weather, forecasts and weather-code parsing through the API layer.',
  },
  {
    name: 'WebSocket',
    description:
      'Live telemetry, positions, pit, weather and now prediction bundle streaming.',
  },
];

const getBadgeTone = (mode: string) => {
  if (mode === 'trained_model') return 'success';
  if (mode === 'heuristic_fallback') return 'warning';
  if (mode === 'rule_based') return 'info';
  return 'default';
};

export default function HelpPage() {
  const [modelStatus, setModelStatus] = useState<ModelStatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadModelStatus = async () => {
      try {
        const payload = await apiFetch<ModelStatusPayload>(
          '/api/predictions/models/status'
        );
        setModelStatus(payload);
      } catch (fetchError) {
        setError(
          fetchError instanceof ApiError
            ? fetchError.message
            : 'Failed to load prediction model status.'
        );
      }
    };

    loadModelStatus();
  }, []);

  return (
    <Layout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Platform Notes"
          title="Help and Data Sources"
          description="Short, honest overview of what this platform uses, what the prediction engine is doing today and what still remains a production risk."
        />

        <div className="panel-grid">
          <StatCard
            label="Prediction Mode"
            value={
              <Badge tone={getBadgeTone(modelStatus?.overall_mode || '')}>
                {modelStatus?.overall_mode || 'Unknown'}
              </Badge>
            }
            helper="Overall runtime behavior of the prediction layer"
            tone="accent"
          />
          <StatCard
            label="Pit Predictor"
            value={
              <Badge tone={getBadgeTone(String(modelStatus?.pit_predictor?.mode || ''))}>
                {String(modelStatus?.pit_predictor?.mode || 'unknown')}
              </Badge>
            }
            helper="Trained model or heuristic fallback"
          />
          <StatCard
            label="Position Model"
            value={
              <Badge tone={getBadgeTone(String(modelStatus?.position_forecaster?.mode || ''))}>
                {String(modelStatus?.position_forecaster?.mode || 'unknown')}
              </Badge>
            }
            helper="Trained model or heuristic fallback"
            tone="warning"
          />
          <StatCard
            label="Strategy Engine"
            value={
              <Badge tone={getBadgeTone(String(modelStatus?.strategy_recommender?.mode || 'rule_based'))}>
                {String(modelStatus?.strategy_recommender?.mode || 'rule_based')}
              </Badge>
            }
            helper="Rule-based strategy analysis"
            tone="success"
          />
        </div>

        {error ? (
          <Surface className="border-red-500/30">
            <p className="text-sm text-red-300">{error}</p>
          </Surface>
        ) : null}

        <Surface
          title="How prediction works, in plain language"
          subtitle="Explained for a non-specialist."
        >
          <div className="space-y-3 text-sm leading-6 text-slate-300">
            <p>
              The platform first looks at the live race snapshot: current lap,
              position, tyre age, recent pace, gaps and weather.
            </p>
            <p>
              Then it estimates three things: who looks close to a pit stop,
              how positions may change over the next laps, and which tyre strategy
              looks safer or more aggressive.
            </p>
            <p>
              Today that system is hybrid. If trained model files are present, the
              pit and position modules use them. If not, they fall back to rules and
              heuristics. Strategy is intentionally rule-based.
            </p>
            <p>
              In simple terms: the app watches the race context and says, for
              example, “these tyres are old, pace is dropping and the pit window is
              close, so this driver is more likely to stop soon.”
            </p>
          </div>
        </Surface>

        <Surface
          title="Integrated Services"
          subtitle="Real services already wired into the current project."
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {integrations.map((integration) => (
              <div
                key={integration.name}
                className="rounded-[22px] border border-white/8 bg-white/[0.03] p-4"
              >
                <p className="font-medium text-white">{integration.name}</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  {integration.description}
                </p>
              </div>
            ))}
          </div>
        </Surface>

        <Surface
          title="Current caveats"
          subtitle="Important limitations that still matter before production."
        >
          <div className="space-y-3 text-sm leading-6 text-slate-300">
            <p>
              OpenF1 free-tier limits remain the main live-data risk. Cache and stale
              fallback help, but they do not remove the upstream dependency.
            </p>
            <p>
              Fantasy endpoints still need frontend/backend contract alignment, so
              they are not part of the main navigation yet.
            </p>
            <p>
              Multi-instance production would still need shared cache or another
              resilience layer, because the current live cache is in-process.
            </p>
          </div>
        </Surface>

        {!modelStatus ? (
          <EmptyState
            title="Model status not loaded yet"
            description="Once the API responds, this page shows whether the current predictions are running on trained models, fallback heuristics or rule-based logic."
          />
        ) : null}
      </div>
    </Layout>
  );
}
