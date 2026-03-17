import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-4xl text-center">
        <h1 className="mb-4 text-6xl font-bold tracking-tight text-white">
          F1 Telemetry Platform
        </h1>
        <p className="mb-8 text-xl text-gray-400">
          Real-time telemetry dashboard and ML-powered predictions for Formula 1
        </p>

        <div className="mb-12 flex justify-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-lg bg-f1-red px-6 py-3 font-semibold text-white transition-colors hover:bg-red-700"
          >
            Live Dashboard
          </Link>
          <Link
            href="/predictions"
            className="rounded-lg border border-white/20 bg-white/10 px-6 py-3 font-semibold text-white backdrop-blur transition-colors hover:bg-white/20"
          >
            Predictions
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-lg bg-gray-800/50 p-6 backdrop-blur">
            <h2 className="mb-2 text-lg font-semibold text-f1-red">Live Telemetry</h2>
            <p className="text-sm text-gray-400">
              Real-time car data including speed, throttle, brake, and gear at 3.7Hz
            </p>
          </div>

          <div className="rounded-lg bg-gray-800/50 p-6 backdrop-blur">
            <h2 className="mb-2 text-lg font-semibold text-f1-red">Track Position</h2>
            <p className="text-sm text-gray-400">
              Live driver positions on track with timing data and gaps
            </p>
          </div>

          <div className="rounded-lg bg-gray-800/50 p-6 backdrop-blur">
            <h2 className="mb-2 text-lg font-semibold text-f1-red">ML Predictions</h2>
            <p className="text-sm text-gray-400">
              AI-powered pit stop and position predictions using Fast-F1
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
