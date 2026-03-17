// Pit Stop Prediction Types
export interface PitPrediction {
  driver_number: number;
  probability: number;
  predicted_lap: number;
  recommended_compound?: string;
  confidence: number;
  reasons: string[];
}

export interface PitPredictionRequest {
  session_key: number;
  driver_number: number;
  current_lap: number;
  current_tyre: string;
  tyre_age: number;
  current_position: number;
  fuel_load?: number;
  degradation_rate?: number;
  gap_to_leader?: number;
}

// Position Forecast Types
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

// Strategy Analysis Types
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

export interface StrategyRequest {
  session_key: number;
  driver_number: number;
  current_lap: number;
  total_laps?: number;
  current_compound: string;
  tyre_age: number;
  position: number;
  track_temp?: number;
  weather?: string;
}

// Aggregated Types
export interface AllPredictionsResponse {
  session_key: number;
  pit_predictions: PitPrediction[];
  position_forecast: PositionForecastResponse;
  generated_at: string;
}

// Model Status Types
export interface ModelStatus {
  pit_predictor: {
    loaded: boolean;
    features: number;
  };
  position_forecaster: {
    loaded: boolean;
    features: number;
  };
  strategy_recommender: {
    loaded: boolean;
    type: string;
  };
  models_loaded: boolean;
}

export interface HistoricalAccuracy {
  model_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  races_analyzed: number;
  last_updated: string;
}

// Real-time Updates
export interface PredictionUpdate {
  type: 'pit_prediction' | 'position_forecast' | 'strategy';
  driver_number: number;
  data: PitPrediction | DriverPositionForecast | StrategyAnalysis;
  timestamp: number;
}
