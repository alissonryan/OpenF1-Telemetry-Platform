// Fantasy F1 Types

// Driver Prediction
export interface FantasyDriverPrediction {
  driver_id: string;
  driver_name: string;
  team_name: string;
  price: number;
  
  predicted_qualifying_position: number;
  predicted_race_position: number;
  predicted_qualifying_points: number;
  predicted_race_points: number;
  predicted_bonus_points: number;
  predicted_total_points: number;
  
  confidence: number;
  points_per_million: number;
  factors: string[];
  
  avg_points_last_5: number;
  season_avg_points: number;
}

// Driver in Team
export interface DriverInTeam {
  driver_id: string;
  driver_name: string;
  team_name: string;
  price: number;
  predicted_total_points: number;
  points_per_million: number;
  confidence: number;
}

// Team Recommendation
export interface TeamRecommendation {
  drivers: DriverInTeam[];
  constructor_id: string;
  constructor_name: string;
  constructor_price: number;
  constructor_predicted_points: number;
  
  total_cost: number;
  total_predicted_points: number;
  budget_remaining: number;
  budget_used_pct: number;
  
  strategy: 'balanced' | 'value' | 'premium';
  confidence: number;
}

// Comparison Result
export interface ComparisonResult {
  driver1: FantasyDriverPrediction;
  driver2: FantasyDriverPrediction;
  
  points_difference: number;
  price_difference: number;
  value_difference: number;
  
  recommendation: string;
  factors: string[];
}

// Differential Pick
export interface DifferentialPick {
  driver: FantasyDriverPrediction;
  ownership_pct: number;
  differential_score: number;
  reasoning: string;
}

// Value Plays Response
export interface ValuePlaysResponse {
  data: FantasyDriverPrediction[];
  total: number;
}

// Scoring System
export interface ScoringSystem {
  qualifying_points: Record<number, number>;
  race_points: Record<number, number>;
  bonus_points: {
    fastest_lap: number;
    pole_position: number;
    driver_of_the_day: number;
    overtake: number;
  };
  rules: Record<string, string>;
}

// Budget Info
export interface BudgetInfo {
  default_budget: number;
  driver_prices: Record<string, number>;
  constructor_prices: Record<string, number>;
  team_composition: {
    drivers: number;
    constructors: number;
  };
}

// Team Builder State
export interface FantasyTeam {
  drivers: FantasyDriverPrediction[];
  constructor_id: string | null;
  constructor_name: string;
  constructor_price: number;
  total_cost: number;
  total_predicted_points: number;
}

// Sort Options
export type SortOption = 'points' | 'value' | 'price' | 'name';
