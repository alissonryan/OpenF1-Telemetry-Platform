'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import PageHeader from '@/components/ui/PageHeader';
import { Surface, StatCard, EmptyState, Badge } from '@/components/ui/Surface';
import { useFantasy } from '@/hooks/useFantasy';
import type {
  FantasyDriverPrediction,
  ComparisonResult,
  SortOption,
} from '@/types/fantasy';

const tabs = [
  { id: 'drivers' as const, label: 'All Drivers' },
  { id: 'team' as const, label: 'Team Builder' },
  { id: 'value' as const, label: 'Value Plays' },
  { id: 'compare' as const, label: 'Compare' },
];

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'points', label: 'Expected Points' },
  { value: 'value', label: 'Points / Million' },
  { value: 'price', label: 'Price' },
  { value: 'name', label: 'Name' },
];

function DriverRow({
  driver,
  onAdd,
  onCompare,
  isInTeam,
  isCompareSelected,
}: {
  driver: FantasyDriverPrediction;
  onAdd?: () => void;
  onCompare?: () => void;
  isInTeam: boolean;
  isCompareSelected: boolean;
}) {
  const confidence = Math.round(driver.confidence * 100);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-4 rounded-2xl border border-white/8 bg-white/[0.03] p-4 transition hover:border-white/15 hover:bg-white/[0.06]"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-white truncate">{driver.driver_name}</p>
          <Badge tone={confidence >= 70 ? 'success' : confidence >= 40 ? 'warning' : 'default'}>
            {confidence}%
          </Badge>
        </div>
        <p className="text-sm text-slate-400 mt-0.5">{driver.team_name}</p>
      </div>

      <div className="hidden sm:flex items-center gap-6 text-sm">
        <div className="text-center">
          <p className="text-slate-400 text-xs">Pts</p>
          <p className="text-white font-semibold">{driver.predicted_total_points.toFixed(1)}</p>
        </div>
        <div className="text-center">
          <p className="text-slate-400 text-xs">Pts/M</p>
          <p className="text-emerald-400 font-semibold">{driver.points_per_million.toFixed(1)}</p>
        </div>
        <div className="text-center">
          <p className="text-slate-400 text-xs">Price</p>
          <p className="text-white font-medium">${driver.price.toFixed(1)}M</p>
        </div>
        <div className="text-center">
          <p className="text-slate-400 text-xs">Qual</p>
          <p className="text-white">P{driver.predicted_qualifying_position}</p>
        </div>
        <div className="text-center">
          <p className="text-slate-400 text-xs">Race</p>
          <p className="text-white">P{driver.predicted_race_position}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {onCompare && (
          <button
            onClick={onCompare}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
              isCompareSelected
                ? 'border-blue-500/40 bg-blue-500/20 text-blue-400'
                : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'
            }`}
          >
            VS
          </button>
        )}
        {onAdd && (
          <button
            onClick={onAdd}
            disabled={isInTeam}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
              isInTeam
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 cursor-default'
                : 'border-f1-red/30 bg-f1-red/10 text-red-300 hover:bg-f1-red/20'
            }`}
          >
            {isInTeam ? 'Added' : '+ Team'}
          </button>
        )}
      </div>
    </motion.div>
  );
}

export default function FantasyPage() {
  const [activeTab, setActiveTab] = useState<'drivers' | 'team' | 'value' | 'compare'>('drivers');
  const [sortBy, setSortBy] = useState<SortOption>('points');
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [strategy, setStrategy] = useState<'balanced' | 'value' | 'premium'>('balanced');

  const {
    drivers,
    teamRecommendation,
    valuePlays,
    differentialPicks,
    myTeam,
    budget,
    budgetRemaining,
    isLoadingDrivers,
    isLoadingRecommendation,
    isLoadingValuePlays,
    isLoadingComparison,
    driversError,
    recommendationError,
    fetchDrivers,
    fetchTeamRecommendation,
    addDriverToTeam,
    removeDriverFromTeam,
    clearTeam,
    compareDrivers,
    refreshAll,
  } = useFantasy();

  const sortedDrivers = useMemo(() => {
    const copy = [...drivers];
    switch (sortBy) {
      case 'points':
        return copy.sort((a, b) => b.predicted_total_points - a.predicted_total_points);
      case 'value':
        return copy.sort((a, b) => b.points_per_million - a.points_per_million);
      case 'price':
        return copy.sort((a, b) => b.price - a.price);
      case 'name':
        return copy.sort((a, b) => a.driver_name.localeCompare(b.driver_name));
      default:
        return copy;
    }
  }, [drivers, sortBy]);

  const handleCompareToggle = (driverId: string) => {
    setCompareIds(prev => {
      if (prev.includes(driverId)) return prev.filter(id => id !== driverId);
      if (prev.length >= 2) return [prev[1], driverId];
      return [...prev, driverId];
    });
    setComparisonResult(null);
  };

  const handleCompare = async () => {
    if (compareIds.length !== 2) return;
    const result = await compareDrivers(compareIds[0], compareIds[1]);
    setComparisonResult(result);
  };

  const handleGetRecommendation = () => {
    fetchTeamRecommendation(strategy);
  };

  const teamDriverIds = new Set(myTeam.drivers.map(d => d.driver_id));

  return (
    <Layout>
      <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6">
        <PageHeader
          eyebrow="Fantasy F1"
          title="Fantasy Team Builder"
          description="Predict driver points, build your team within budget, and find value plays using AI-powered predictions."
          actions={
            <button
              onClick={refreshAll}
              disabled={isLoadingDrivers}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/10 disabled:opacity-50"
            >
              {isLoadingDrivers ? 'Loading...' : 'Refresh'}
            </button>
          }
        />

        {/* Stats Row */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Budget" value={`$${budget.toFixed(1)}M`} tone="default" />
          <StatCard
            label="Remaining"
            value={`$${budgetRemaining.toFixed(1)}M`}
            tone={budgetRemaining < 10 ? 'warning' : 'success'}
          />
          <StatCard
            label="Team Size"
            value={`${myTeam.drivers.length}/5`}
            tone={myTeam.drivers.length === 5 ? 'success' : 'default'}
          />
          <StatCard
            label="Predicted Pts"
            value={myTeam.total_predicted_points.toFixed(1)}
            tone="accent"
          />
        </div>

        {/* Tabs */}
        <div className="flex gap-2 overflow-x-auto rounded-2xl border border-white/10 bg-white/5 p-1.5">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 rounded-xl px-4 py-2 text-sm font-medium transition whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-f1-red text-white shadow-lg shadow-f1-red/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Error */}
        {driversError && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
            Failed to load drivers: {driversError}.{' '}
            <button onClick={() => fetchDrivers()} className="underline hover:text-white">
              Retry
            </button>
          </div>
        )}

        <AnimatePresence mode="wait">
          {/* TAB: All Drivers */}
          {activeTab === 'drivers' && (
            <motion.div
              key="drivers"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <Surface
                title="Driver Predictions"
                subtitle="Predicted fantasy points for each driver"
                actions={
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-400">Sort:</label>
                    <select
                      value={sortBy}
                      onChange={e => {
                        setSortBy(e.target.value as SortOption);
                        fetchDrivers(e.target.value as SortOption);
                      }}
                      className="rounded-lg border border-white/10 bg-slate-900 px-3 py-1.5 text-sm text-white"
                    >
                      {sortOptions.map(opt => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                }
              >
                {isLoadingDrivers && drivers.length === 0 ? (
                  <div className="space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="h-16 animate-pulse rounded-2xl bg-white/5" />
                    ))}
                  </div>
                ) : drivers.length === 0 ? (
                  <EmptyState
                    title="No driver data"
                    description="The Fantasy predictor could not load driver predictions. Make sure the API is running."
                  />
                ) : (
                  <div className="space-y-2">
                    {sortedDrivers.map(driver => (
                      <DriverRow
                        key={driver.driver_id}
                        driver={driver}
                        onAdd={() => addDriverToTeam(driver)}
                        onCompare={() => handleCompareToggle(driver.driver_id)}
                        isInTeam={teamDriverIds.has(driver.driver_id)}
                        isCompareSelected={compareIds.includes(driver.driver_id)}
                      />
                    ))}
                  </div>
                )}
              </Surface>
            </motion.div>
          )}

          {/* TAB: Team Builder */}
          {activeTab === 'team' && (
            <motion.div
              key="team"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* My Team */}
              <Surface
                title="My Team"
                subtitle={`${myTeam.drivers.length}/5 drivers selected`}
                actions={
                  <div className="flex gap-2">
                    <button
                      onClick={clearTeam}
                      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10"
                    >
                      Clear
                    </button>
                  </div>
                }
              >
                {myTeam.drivers.length === 0 ? (
                  <EmptyState
                    title="No drivers selected"
                    description="Go to the All Drivers tab and click '+ Team' to add drivers to your squad."
                  />
                ) : (
                  <div className="space-y-2">
                    {myTeam.drivers.map(driver => (
                      <div
                        key={driver.driver_id}
                        className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] p-4"
                      >
                        <div>
                          <p className="font-semibold text-white">{driver.driver_name}</p>
                          <p className="text-sm text-slate-400">{driver.team_name}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right text-sm">
                            <p className="text-white font-semibold">
                              {driver.predicted_total_points.toFixed(1)} pts
                            </p>
                            <p className="text-slate-400">${driver.price.toFixed(1)}M</p>
                          </div>
                          <button
                            onClick={() => removeDriverFromTeam(driver.driver_id)}
                            className="rounded-lg border border-red-500/20 bg-red-500/10 p-2 text-red-400 hover:bg-red-500/20"
                          >
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                    <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-4 text-center">
                      <p className="text-sm text-slate-400">
                        Total: <span className="text-white font-semibold">${myTeam.total_cost.toFixed(1)}M</span>
                        {' | '}
                        Predicted: <span className="text-emerald-400 font-semibold">{myTeam.total_predicted_points.toFixed(1)} pts</span>
                      </p>
                    </div>
                  </div>
                )}
              </Surface>

              {/* AI Recommendation */}
              <Surface
                title="AI Team Recommendation"
                subtitle="Let AI build the optimal team for your budget"
                actions={
                  <div className="flex items-center gap-2">
                    <select
                      value={strategy}
                      onChange={e => setStrategy(e.target.value as 'balanced' | 'value' | 'premium')}
                      className="rounded-lg border border-white/10 bg-slate-900 px-3 py-1.5 text-sm text-white"
                    >
                      <option value="balanced">Balanced</option>
                      <option value="value">Value</option>
                      <option value="premium">Premium</option>
                    </select>
                    <button
                      onClick={handleGetRecommendation}
                      disabled={isLoadingRecommendation}
                      className="rounded-lg border border-f1-red/30 bg-f1-red/10 px-4 py-1.5 text-sm font-medium text-red-300 hover:bg-f1-red/20 disabled:opacity-50"
                    >
                      {isLoadingRecommendation ? 'Calculating...' : 'Get Recommendation'}
                    </button>
                  </div>
                }
              >
                {recommendationError && (
                  <div className="mb-4 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-300">
                    {recommendationError}
                  </div>
                )}
                {teamRecommendation ? (
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-3 mb-4">
                      <Badge tone="success">
                        Strategy: {teamRecommendation.strategy}
                      </Badge>
                      <Badge tone="info">
                        Budget used: {teamRecommendation.budget_used_pct.toFixed(0)}%
                      </Badge>
                      <Badge>
                        Confidence: {Math.round(teamRecommendation.confidence * 100)}%
                      </Badge>
                    </div>
                    {teamRecommendation.drivers.map(driver => (
                      <div
                        key={driver.driver_id}
                        className="flex items-center justify-between rounded-xl border border-emerald-500/10 bg-emerald-500/5 p-3"
                      >
                        <div>
                          <p className="font-medium text-white">{driver.driver_name}</p>
                          <p className="text-sm text-slate-400">{driver.team_name}</p>
                        </div>
                        <div className="text-right text-sm">
                          <p className="text-emerald-400 font-semibold">
                            {driver.predicted_total_points.toFixed(1)} pts
                          </p>
                          <p className="text-slate-400">${driver.price.toFixed(1)}M</p>
                        </div>
                      </div>
                    ))}
                    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-center">
                      <p className="text-sm text-emerald-300">
                        Total: ${teamRecommendation.total_cost.toFixed(1)}M |{' '}
                        Predicted: {teamRecommendation.total_predicted_points.toFixed(1)} pts |{' '}
                        Remaining: ${teamRecommendation.budget_remaining.toFixed(1)}M
                      </p>
                    </div>
                  </div>
                ) : (
                  <EmptyState
                    title="No recommendation yet"
                    description="Select a strategy and click 'Get Recommendation' to let AI build the optimal team."
                  />
                )}
              </Surface>
            </motion.div>
          )}

          {/* TAB: Value Plays */}
          {activeTab === 'value' && (
            <motion.div
              key="value"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <Surface
                title="Value Plays"
                subtitle="Highest points-per-million drivers — best bang for your budget"
              >
                {isLoadingValuePlays && valuePlays.length === 0 ? (
                  <div className="space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="h-16 animate-pulse rounded-2xl bg-white/5" />
                    ))}
                  </div>
                ) : valuePlays.length === 0 ? (
                  <EmptyState
                    title="No value plays available"
                    description="Value plays data could not be loaded."
                  />
                ) : (
                  <div className="space-y-2">
                    {valuePlays.map((driver, idx) => (
                      <div
                        key={driver.driver_id}
                        className="flex items-center gap-4 rounded-2xl border border-white/8 bg-white/[0.03] p-4"
                      >
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/20 text-sm font-bold text-emerald-400">
                          {idx + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-white">{driver.driver_name}</p>
                          <p className="text-sm text-slate-400">{driver.team_name}</p>
                        </div>
                        <div className="flex items-center gap-6 text-sm">
                          <div className="text-center">
                            <p className="text-xs text-slate-400">Value</p>
                            <p className="text-emerald-400 font-bold">{driver.points_per_million.toFixed(1)}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-slate-400">Pts</p>
                            <p className="text-white font-semibold">{driver.predicted_total_points.toFixed(1)}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-slate-400">Price</p>
                            <p className="text-white">${driver.price.toFixed(1)}M</p>
                          </div>
                        </div>
                        <button
                          onClick={() => addDriverToTeam(driver)}
                          disabled={teamDriverIds.has(driver.driver_id)}
                          className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                            teamDriverIds.has(driver.driver_id)
                              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                              : 'border-f1-red/30 bg-f1-red/10 text-red-300 hover:bg-f1-red/20'
                          }`}
                        >
                          {teamDriverIds.has(driver.driver_id) ? 'Added' : '+ Team'}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </Surface>

              {/* Differential Picks */}
              <Surface
                title="Differential Picks"
                subtitle="Lower-owned drivers with high upside potential"
              >
                {differentialPicks.length === 0 ? (
                  <EmptyState
                    title="No differential picks"
                    description="Differential picks could not be loaded."
                  />
                ) : (
                  <div className="space-y-2">
                    {differentialPicks.map(pick => (
                      <div
                        key={pick.driver.driver_id}
                        className="flex items-center gap-4 rounded-2xl border border-white/8 bg-white/[0.03] p-4"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-white">{pick.driver.driver_name}</p>
                            <Badge tone="info">{pick.ownership_pct.toFixed(0)}% owned</Badge>
                          </div>
                          <p className="text-sm text-slate-400 mt-1">{pick.reasoning}</p>
                        </div>
                        <div className="text-right text-sm">
                          <p className="text-amber-400 font-semibold">Score: {pick.differential_score.toFixed(1)}</p>
                          <p className="text-slate-400">${pick.driver.price.toFixed(1)}M</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Surface>
            </motion.div>
          )}

          {/* TAB: Compare */}
          {activeTab === 'compare' && (
            <motion.div
              key="compare"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <Surface
                title="Driver Comparison"
                subtitle="Select two drivers to compare"
                actions={
                  compareIds.length === 2 ? (
                    <button
                      onClick={handleCompare}
                      disabled={isLoadingComparison}
                      className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-sm font-medium text-blue-300 hover:bg-blue-500/20 disabled:opacity-50"
                    >
                      {isLoadingComparison ? 'Comparing...' : 'Compare Now'}
                    </button>
                  ) : undefined
                }
              >
                <div className="mb-4">
                  <p className="text-sm text-slate-400">
                    {compareIds.length === 0 && 'Click "VS" on two drivers below to select them.'}
                    {compareIds.length === 1 && 'Select one more driver to compare.'}
                    {compareIds.length === 2 && 'Ready to compare! Click "Compare Now" above.'}
                  </p>
                </div>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {sortedDrivers.map(driver => (
                    <DriverRow
                      key={driver.driver_id}
                      driver={driver}
                      onCompare={() => handleCompareToggle(driver.driver_id)}
                      isInTeam={false}
                      isCompareSelected={compareIds.includes(driver.driver_id)}
                    />
                  ))}
                </div>
              </Surface>

              {/* Comparison Result */}
              {comparisonResult && (
                <Surface title="Comparison Result">
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    {[comparisonResult.driver1, comparisonResult.driver2].map((driver, idx) => (
                      <div
                        key={driver.driver_id}
                        className={`rounded-2xl border p-5 ${
                          idx === 0
                            ? 'border-blue-500/20 bg-blue-500/5'
                            : 'border-amber-500/20 bg-amber-500/5'
                        }`}
                      >
                        <p className="text-lg font-semibold text-white">{driver.driver_name}</p>
                        <p className="text-sm text-slate-400 mb-3">{driver.team_name}</p>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div>
                            <p className="text-slate-400">Points</p>
                            <p className="text-white font-semibold">{driver.predicted_total_points.toFixed(1)}</p>
                          </div>
                          <div>
                            <p className="text-slate-400">Price</p>
                            <p className="text-white font-semibold">${driver.price.toFixed(1)}M</p>
                          </div>
                          <div>
                            <p className="text-slate-400">Value</p>
                            <p className="text-emerald-400 font-semibold">{driver.points_per_million.toFixed(1)}</p>
                          </div>
                          <div>
                            <p className="text-slate-400">Confidence</p>
                            <p className="text-white">{Math.round(driver.confidence * 100)}%</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="text-sm font-medium text-white mb-2">Recommendation</p>
                    <p className="text-sm text-slate-300">{comparisonResult.recommendation}</p>
                    {comparisonResult.factors.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {comparisonResult.factors.map((factor, i) => (
                          <Badge key={i} tone="info">{factor}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </Surface>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Layout>
  );
}
