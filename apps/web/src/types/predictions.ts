export interface PitPrediction {
  driver_number: number;
  probability: number;
  predicted_lap: number;
  confidence: number;
  reasons: string[];
}

export interface PositionForecast {
  driver_number: number;
  current_position: number;
  predicted_position: number;
  position_change: number;
  confidence: number;
}

export interface StrategyAnalysis {
  driver_number: number;
  current_tyre: string;
  tyre_age: number;
  recommended_stops: number;
  optimal_lap_window: [number, number];
  risk_level: 'low' | 'medium' | 'high';
}
