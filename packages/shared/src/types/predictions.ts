// Prediction types shared between frontend and backend

export interface PitPrediction {
  driver_number: number;
  probability: number;
  predicted_lap: number;
  recommended_compound?: string;
  confidence: number;
  reasons: string[];
}

export interface DriverPositionForecast {
  driver_number: number;
  driver_name?: string;
  team_name?: string;
  current_position: number;
  predicted_position: number;
  position_change: number;
  confidence: number;
  factors?: string[];
}

export interface PositionForecastResponse {
  session_key: number;
  current_lap?: number;
  total_laps?: number;
  predictions: DriverPositionForecast[];
  generated_at?: string;
}

export interface StrategyAlternative {
  strategy: string;
  risk: string;
  expected_gain?: number;
  condition?: string;
}

export interface StrategyAnalysis {
  driver_number: number;
  current_compound: string;
  tyre_age: number;
  recommended_stops: number;
  optimal_laps: number[];
  compounds: string[];
  risk_level: 'low' | 'medium' | 'high';
  expected_positions_gained: number;
  confidence: number;
  alternative_strategies: StrategyAlternative[];
  factors: string[];
}

export interface AllPredictionsResponse {
  session_key: number;
  pit_predictions: PitPrediction[];
  position_forecast: PositionForecastResponse;
  generated_at: string;
}
