'use client';

import { useEffect, useState } from 'react';
import Layout from '@/components/layout/Layout';
import PageHeader from '@/components/ui/PageHeader';
import { StatCard, Surface } from '@/components/ui/Surface';

interface LocalPreferences {
  autoRefresh: boolean;
  compactPanels: boolean;
  reducedMotion: boolean;
}

const STORAGE_KEY = 'f1-platform-settings';

const defaultPreferences: LocalPreferences = {
  autoRefresh: true,
  compactPanels: false,
  reducedMotion: false,
};

export default function SettingsPage() {
  const [preferences, setPreferences] =
    useState<LocalPreferences>(defaultPreferences);

  useEffect(() => {
    const rawValue = window.localStorage.getItem(STORAGE_KEY);
    if (!rawValue) {
      return;
    }

    try {
      setPreferences({
        ...defaultPreferences,
        ...(JSON.parse(rawValue) as Partial<LocalPreferences>),
      });
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const updatePreference = <K extends keyof LocalPreferences>(
    key: K,
    value: LocalPreferences[K]
  ) => {
    const next = { ...preferences, [key]: value };
    setPreferences(next);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  };

  return (
    <Layout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Local Preferences"
          title="Workspace Settings"
          description="These controls are local to this browser session. They do not modify backend behavior or deployment configuration."
        />

        <div className="panel-grid">
          <StatCard
            label="API URL"
            value={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
            helper="Frontend runtime target for REST requests"
            tone="accent"
          />
          <StatCard
            label="WS URL"
            value={process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'}
            helper="Frontend runtime target for live WebSocket data"
          />
          <StatCard
            label="Auto Refresh"
            value={preferences.autoRefresh ? 'On' : 'Off'}
            helper="Client-side preference only"
            tone="success"
          />
          <StatCard
            label="Motion"
            value={preferences.reducedMotion ? 'Reduced' : 'Standard'}
            helper="Local visual preference"
            tone="warning"
          />
        </div>

        <Surface
          title="Experience Controls"
          subtitle="Persisted to local storage for this browser only."
        >
          <div className="grid gap-4 md:grid-cols-3">
            <PreferenceToggle
              title="Auto refresh"
              description="Keep client pages polling and refreshing automatically where supported."
              checked={preferences.autoRefresh}
              onChange={(value) => updatePreference('autoRefresh', value)}
            />
            <PreferenceToggle
              title="Compact panels"
              description="Reserve this toggle for a future denser layout mode."
              checked={preferences.compactPanels}
              onChange={(value) => updatePreference('compactPanels', value)}
            />
            <PreferenceToggle
              title="Reduced motion"
              description="Reserve this toggle for calmer transitions in a future pass."
              checked={preferences.reducedMotion}
              onChange={(value) => updatePreference('reducedMotion', value)}
            />
          </div>
        </Surface>

        <Surface
          title="Environment Notes"
          subtitle="Operational reminders before staging or production."
        >
          <div className="space-y-3 text-sm leading-6 text-slate-300">
            <p>
              `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` are read at build/runtime
              by the frontend. This page only shows their effective values.
            </p>
            <p>
              OpenF1 remains the main live upstream. Cache and stale fallback reduce
              pressure, but production still needs explicit upstream resilience.
            </p>
            <p>
              FastF1 and F1DB depend on local cache/database availability on the API
              side. This page does not edit those backend paths.
            </p>
          </div>
        </Surface>
      </div>
    </Layout>
  );
}

function PreferenceToggle({
  title,
  description,
  checked,
  onChange,
}: {
  title: string;
  description: string;
  checked: boolean;
  onChange: (nextValue: boolean) => void;
}) {
  return (
    <div className="rounded-[22px] border border-white/8 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-white">{title}</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
        </div>
        <button
          type="button"
          onClick={() => onChange(!checked)}
          className={`relative h-7 w-12 rounded-full transition-colors ${
            checked ? 'bg-f1-red' : 'bg-slate-700'
          }`}
          aria-pressed={checked}
          aria-label={title}
        >
          <span
            className={`absolute top-1 h-5 w-5 rounded-full bg-white transition-transform ${
              checked ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>
    </div>
  );
}
