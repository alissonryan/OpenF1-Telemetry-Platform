import Link from 'next/link';
import { primaryNavigation } from '@/lib/navigation';

const highlights = [
  {
    title: 'Live Control',
    description:
      'OpenF1-backed workspace for current sessions, positions, intervals, telemetry and race control.',
  },
  {
    title: 'Historical Lab',
    description:
      'FastF1 analysis for past sessions with telemetry traces, comparison and weather summaries.',
  },
  {
    title: 'Prediction Layer',
    description:
      'Hybrid pit, position and strategy forecasts built from live session context and available model artifacts.',
  },
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden px-6 py-10 sm:px-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(232,0,32,0.14),transparent_25%),radial-gradient(circle_at_bottom_left,rgba(56,189,248,0.12),transparent_22%)]" />
      <div className="relative mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl flex-col justify-center gap-12">
        <section className="grid gap-10 xl:grid-cols-[1.2fr_0.8fr] xl:items-end">
          <div className="space-y-6">
            <p className="font-mono text-xs uppercase tracking-[0.36em] text-red-200/80">
              OpenF1 Telemetry Platform
            </p>
            <div className="space-y-5">
              <h1 className="font-display text-6xl uppercase leading-none tracking-[0.03em] text-white sm:text-7xl xl:text-8xl">
                One workspace for live telemetry, history and race intelligence.
              </h1>
              <p className="max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
                This project combines OpenF1 live data, FastF1 historical analysis,
                F1DB archive data and Open-Meteo weather into a single Formula 1
                workspace. The navigation below now reflects real pages backed by
                real integrations.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                href="/dashboard"
                className="rounded-full bg-f1-red px-6 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-white transition-transform hover:-translate-y-0.5"
              >
                Open Dashboard
              </Link>
              <Link
                href="/historical"
                className="rounded-full border border-white/15 bg-white/5 px-6 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-white transition-colors hover:border-white/30 hover:bg-white/10"
              >
                Explore History
              </Link>
            </div>
          </div>

          <div className="grid gap-4">
            {highlights.map((highlight) => (
              <div
                key={highlight.title}
                className="rounded-[28px] border border-white/10 bg-white/[0.05] p-6 backdrop-blur-xl"
              >
                <p className="font-display text-2xl uppercase tracking-[0.05em] text-white">
                  {highlight.title}
                </p>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {highlight.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {primaryNavigation.map((item, index) => (
            <Link
              key={item.href}
              href={item.href}
              className="group rounded-[26px] border border-white/10 bg-slate-950/50 p-6 backdrop-blur-xl transition-colors hover:border-white/25 hover:bg-white/[0.06]"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-display text-3xl uppercase tracking-[0.05em] text-white">
                    {item.label}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-400">
                    {item.description}
                  </p>
                </div>
                <span className="font-mono text-xs uppercase tracking-[0.24em] text-slate-500">
                  0{index + 1}
                </span>
              </div>
              <div className="mt-6 flex items-center justify-between text-sm text-slate-300">
                <span>Open module</span>
                <span className="transition-transform group-hover:translate-x-1">
                  →
                </span>
              </div>
            </Link>
          ))}
        </section>
      </div>
    </main>
  );
}
