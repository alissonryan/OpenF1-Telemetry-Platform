'use client';

import { useState, useEffect, useCallback } from 'react';
import type {
  FantasyDriverPrediction,
  TeamRecommendation,
  ComparisonResult,
  DifferentialPick,
  ScoringSystem,
  BudgetInfo,
  FantasyTeam,
  SortOption,
} from '@/types/fantasy';

interface UseFantasyOptions {
  autoLoadDrivers?: boolean;
  circuitId?: string;
}

interface UseFantasyReturn {
  // Data
  drivers: FantasyDriverPrediction[];
  teamRecommendation: TeamRecommendation | null;
  valuePlays: FantasyDriverPrediction[];
  differentialPicks: DifferentialPick[];
  scoringSystem: ScoringSystem | null;
  budgetInfo: BudgetInfo | null;
  
  // Team Builder State
  myTeam: FantasyTeam;
  budget: number;
  budgetRemaining: number;
  
  // Loading States
  isLoadingDrivers: boolean;
  isLoadingRecommendation: boolean;
  isLoadingValuePlays: boolean;
  isLoadingComparison: boolean;
  
  // Errors
  driversError: string | null;
  recommendationError: string | null;
  
  // Actions
  fetchDrivers: (sortBy?: SortOption) => Promise<void>;
  fetchTeamRecommendation: (strategy?: 'balanced' | 'value' | 'premium') => Promise<void>;
  fetchValuePlays: (limit?: number) => Promise<void>;
  fetchDifferentialPicks: (budgetAfterCore?: number) => Promise<void>;
  compareDrivers: (driver1Id: string, driver2Id: string) => Promise<ComparisonResult | null>;
  predictDriver: (driverId: string) => Promise<FantasyDriverPrediction | null>;
  
  // Team Builder Actions
  addDriverToTeam: (driver: FantasyDriverPrediction) => boolean;
  removeDriverFromTeam: (driverId: string) => void;
  setConstructor: (id: string, name: string, price: number) => void;
  clearTeam: () => void;
  setBudget: (budget: number) => void;
  
  // Utilities
  refreshAll: () => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Map backend FantasyPrediction schema to frontend FantasyDriverPrediction
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapPrediction(raw: any): FantasyDriverPrediction {
  return {
    driver_id: String(raw.driver_id),
    driver_name: raw.driver_name ?? `Driver ${raw.driver_id}`,
    team_name: raw.team_name ?? '',
    price: raw.price ?? 0,
    predicted_qualifying_position: raw.expected_qualifying_position ?? 0,
    predicted_race_position: raw.expected_race_position ?? 0,
    predicted_qualifying_points: raw.qualifying_points ?? 0,
    predicted_race_points: raw.race_points ?? 0,
    predicted_bonus_points: raw.bonus_points ?? 0,
    predicted_total_points: raw.total_expected_points ?? 0,
    confidence: raw.confidence ?? 0,
    points_per_million: raw.points_per_million ?? 0,
    factors: raw.reasons ?? [],
    avg_points_last_5: raw.total_expected_points ?? 0,
    season_avg_points: raw.total_expected_points ?? 0,
  };
}

const DEFAULT_BUDGET = 100.0;
const MAX_DRIVERS = 5;

export function useFantasy(options: UseFantasyOptions = {}): UseFantasyReturn {
  const { autoLoadDrivers = true, circuitId } = options;
  
  // Data State
  const [drivers, setDrivers] = useState<FantasyDriverPrediction[]>([]);
  const [teamRecommendation, setTeamRecommendation] = useState<TeamRecommendation | null>(null);
  const [valuePlays, setValuePlays] = useState<FantasyDriverPrediction[]>([]);
  const [differentialPicks, setDifferentialPicks] = useState<DifferentialPick[]>([]);
  const [scoringSystem, setScoringSystem] = useState<ScoringSystem | null>(null);
  const [budgetInfo, setBudgetInfo] = useState<BudgetInfo | null>(null);
  
  // Team Builder State
  const [myTeam, setMyTeam] = useState<FantasyTeam>({
    drivers: [],
    constructor_id: null,
    constructor_name: '',
    constructor_price: 0,
    total_cost: 0,
    total_predicted_points: 0,
  });
  const [budget, setBudgetState] = useState(DEFAULT_BUDGET);
  
  // Loading States
  const [isLoadingDrivers, setIsLoadingDrivers] = useState(false);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false);
  const [isLoadingValuePlays, setIsLoadingValuePlays] = useState(false);
  const [isLoadingComparison, setIsLoadingComparison] = useState(false);
  
  // Error States
  const [driversError, setDriversError] = useState<string | null>(null);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  
  // Computed
  const budgetRemaining = budget - myTeam.total_cost;
  
  // Fetch all drivers
  const fetchDrivers = useCallback(async (sortBy: SortOption = 'points') => {
    setIsLoadingDrivers(true);
    setDriversError(null);

    try {
      const params = new URLSearchParams();
      if (circuitId) {
        params.append('circuit_id', circuitId);
      }

      const response = await fetch(`${API_BASE}/api/fantasy/predict/all?${params}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const raw = await response.json();
      const data: FantasyDriverPrediction[] = raw.map(mapPrediction);

      // Sort client-side since backend always sorts by expected points
      if (sortBy === 'price') {
        data.sort((a, b) => b.price - a.price);
      } else if (sortBy === 'value') {
        data.sort((a, b) => b.points_per_million - a.points_per_million);
      }

      setDrivers(data);
    } catch (err) {
      console.error('Failed to fetch drivers:', err);
      setDriversError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoadingDrivers(false);
    }
  }, [circuitId]);
  
  // Fetch team recommendation
  const fetchTeamRecommendation = useCallback(async (strategy: 'balanced' | 'value' | 'premium' = 'balanced') => {
    setIsLoadingRecommendation(true);
    setRecommendationError(null);
    
    try {
      const params = new URLSearchParams({
        budget: budget.toString(),
        strategy,
      });
      if (circuitId) {
        params.append('circuit_id', circuitId);
      }
      
      const response = await fetch(`${API_BASE}/api/fantasy/recommend?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data: TeamRecommendation = await response.json();
      setTeamRecommendation(data);
    } catch (err) {
      console.error('Failed to fetch team recommendation:', err);
      setRecommendationError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoadingRecommendation(false);
    }
  }, [budget, circuitId]);
  
  // Fetch value plays
  const fetchValuePlays = useCallback(async (limit: number = 10) => {
    setIsLoadingValuePlays(true);

    try {
      const response = await fetch(`${API_BASE}/api/fantasy/value-plays?limit=${limit}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Backend returns List[FantasyPrediction] directly
      const raw = await response.json();
      setValuePlays(raw.map(mapPrediction));
    } catch (err) {
      console.error('Failed to fetch value plays:', err);
    } finally {
      setIsLoadingValuePlays(false);
    }
  }, []);
  
  // Fetch differential picks
  const fetchDifferentialPicks = useCallback(async (budgetAfterCore: number = 30) => {
    try {
      const params = new URLSearchParams({ budget_after_core: budgetAfterCore.toString() });

      const response = await fetch(`${API_BASE}/api/fantasy/differential?${params}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const rawDiffs = data.differentials ?? [];
      // Map raw FantasyPrediction to DifferentialPick shape
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const mapped: DifferentialPick[] = rawDiffs.map((raw: any) => ({
        driver: mapPrediction(raw),
        ownership_pct: raw.confidence ? (1 - raw.confidence) * 100 : 50,
        differential_score: raw.points_per_million ?? 0,
        reasoning: raw.reasons?.[0] ?? raw.risk_level ?? 'Differential pick',
      }));
      setDifferentialPicks(mapped);
    } catch (err) {
      console.error('Failed to fetch differential picks:', err);
    }
  }, []);
  
  // Compare two drivers
  const compareDrivers = useCallback(async (driver1Id: string, driver2Id: string): Promise<ComparisonResult | null> => {
    setIsLoadingComparison(true);
    
    try {
      const params = new URLSearchParams();
      if (circuitId) {
        params.append('circuit_id', circuitId);
      }
      
      const response = await fetch(
        `${API_BASE}/api/fantasy/compare/${driver1Id}/${driver2Id}?${params}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (err) {
      console.error('Failed to compare drivers:', err);
      return null;
    } finally {
      setIsLoadingComparison(false);
    }
  }, [circuitId]);
  
  // Predict single driver
  const predictDriver = useCallback(async (driverId: string): Promise<FantasyDriverPrediction | null> => {
    try {
      const params = new URLSearchParams();
      if (circuitId) {
        params.append('circuit_id', circuitId);
      }
      
      const response = await fetch(`${API_BASE}/api/fantasy/predict/${driverId}?${params}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (err) {
      console.error('Failed to predict driver:', err);
      return null;
    }
  }, [circuitId]);
  
  // Scoring system (static - no backend endpoint)
  const fetchScoringSystem = useCallback(async () => {
    setScoringSystem({
      qualifying_points: { 1: 10, 2: 9, 3: 8, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1 },
      race_points: { 1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1 },
      bonus_points: {
        fastest_lap: 5,
        pole_position: 5,
        driver_of_the_day: 10,
        overtake: 2,
      },
      rules: {
        team_size: '5 drivers + 1 constructor',
        budget_cap: '100M',
        transfers: '3 free transfers per race week',
      },
    });
  }, []);
  
  // Fetch budget info from /prices endpoint
  const fetchBudgetInfo = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/fantasy/prices`);
      if (response.ok) {
        const data = await response.json();
        setBudgetInfo({
          default_budget: DEFAULT_BUDGET,
          driver_prices: data.drivers ?? {},
          constructor_prices: data.constructors ?? {},
          team_composition: {
            drivers: MAX_DRIVERS,
            constructors: 1,
          },
        });
      }
    } catch (err) {
      console.error('Failed to fetch budget info:', err);
    }
  }, []);
  
  // Team Builder Actions
  const addDriverToTeam = useCallback((driver: FantasyDriverPrediction): boolean => {
    if (myTeam.drivers.length >= MAX_DRIVERS) {
      return false;
    }
    
    if (myTeam.drivers.some(d => d.driver_id === driver.driver_id)) {
      return false;
    }
    
    const newCost = myTeam.total_cost + driver.price;
    if (newCost > budget) {
      return false;
    }
    
    setMyTeam(prev => ({
      ...prev,
      drivers: [...prev.drivers, driver],
      total_cost: newCost,
      total_predicted_points: prev.total_predicted_points + driver.predicted_total_points,
    }));
    
    return true;
  }, [myTeam, budget]);
  
  const removeDriverFromTeam = useCallback((driverId: string) => {
    setMyTeam(prev => {
      const driver = prev.drivers.find(d => d.driver_id === driverId);
      if (!driver) return prev;
      
      return {
        ...prev,
        drivers: prev.drivers.filter(d => d.driver_id !== driverId),
        total_cost: prev.total_cost - driver.price,
        total_predicted_points: prev.total_predicted_points - driver.predicted_total_points,
      };
    });
  }, []);
  
  const setConstructor = useCallback((id: string, name: string, price: number) => {
    setMyTeam(prev => {
      const costDiff = price - prev.constructor_price;
      return {
        ...prev,
        constructor_id: id,
        constructor_name: name,
        constructor_price: price,
        total_cost: prev.total_cost + costDiff,
      };
    });
  }, []);
  
  const clearTeam = useCallback(() => {
    setMyTeam({
      drivers: [],
      constructor_id: null,
      constructor_name: '',
      constructor_price: 0,
      total_cost: 0,
      total_predicted_points: 0,
    });
  }, []);
  
  const setBudget = useCallback((newBudget: number) => {
    setBudgetState(newBudget);
  }, []);
  
  // Refresh all data
  const refreshAll = useCallback(async () => {
    await Promise.all([
      fetchDrivers(),
      fetchValuePlays(),
      fetchDifferentialPicks(),
      fetchScoringSystem(),
      fetchBudgetInfo(),
    ]);
  }, [fetchDrivers, fetchValuePlays, fetchDifferentialPicks, fetchScoringSystem, fetchBudgetInfo]);
  
  // Initial load
  useEffect(() => {
    if (autoLoadDrivers) {
      fetchDrivers();
      fetchValuePlays();
      fetchDifferentialPicks();
      fetchScoringSystem();
      fetchBudgetInfo();
    }
  }, [autoLoadDrivers, fetchDrivers, fetchValuePlays, fetchDifferentialPicks, fetchScoringSystem, fetchBudgetInfo]);
  
  return {
    // Data
    drivers,
    teamRecommendation,
    valuePlays,
    differentialPicks,
    scoringSystem,
    budgetInfo,
    
    // Team Builder State
    myTeam,
    budget,
    budgetRemaining,
    
    // Loading States
    isLoadingDrivers,
    isLoadingRecommendation,
    isLoadingValuePlays,
    isLoadingComparison,
    
    // Errors
    driversError,
    recommendationError,
    
    // Actions
    fetchDrivers,
    fetchTeamRecommendation,
    fetchValuePlays,
    fetchDifferentialPicks,
    compareDrivers,
    predictDriver,
    
    // Team Builder Actions
    addDriverToTeam,
    removeDriverFromTeam,
    setConstructor,
    clearTeam,
    setBudget,
    
    // Utilities
    refreshAll,
  };
}

export default useFantasy;
