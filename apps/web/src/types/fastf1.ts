export interface FastF1SessionInfo {
  year: number;
  grand_prix: string;
  session_type: string;
  session_name: string;
  date?: string | null;
  total_laps: number;
  drivers: string[];
  circuit_name?: string | null;
  country?: string | null;
}

export interface FastF1TelemetryPoint {
  time: number;
  speed: number;
  throttle: number;
  brake: boolean;
  n_gear: number;
  rpm: number;
  drs?: number | null;
  distance?: number | null;
  driver: string;
  lap_number: number;
}

export interface FastF1TelemetryResponse {
  session_info: FastF1SessionInfo;
  driver: string;
  lap_number: number;
  data: FastF1TelemetryPoint[];
  total_samples: number;
}

export interface FastF1LapData {
  driver: string;
  lap_number: number;
  lap_time?: number | null;
  sector_1?: number | null;
  sector_2?: number | null;
  sector_3?: number | null;
  tyre_compound?: string | null;
  tyre_life?: number | null;
  is_personal_best?: boolean;
  is_fresh_tyre?: boolean;
}

export interface FastF1LapsResponse {
  session_info: FastF1SessionInfo;
  laps: FastF1LapData[];
  total_laps: number;
}

export interface FastF1WeatherSummaryMetric {
  min: number;
  max: number;
  avg: number;
}

export interface FastF1WeatherResponse {
  session_info: FastF1SessionInfo;
  data: Array<{
    time?: number | null;
    air_temp?: number | null;
    track_temp?: number | null;
    humidity?: number | null;
    pressure?: number | null;
    rainfall?: boolean | number | null;
    wind_direction?: number | null;
    wind_speed?: number | null;
  }>;
  summary: {
    air_temp?: FastF1WeatherSummaryMetric;
    track_temp?: FastF1WeatherSummaryMetric;
    humidity?: FastF1WeatherSummaryMetric;
    wind_speed?: FastF1WeatherSummaryMetric;
    rainfall?: boolean;
  };
}

export interface FastF1FastestLap {
  driver?: string;
  lap_number?: number;
  lap_time?: string;
  lap_time_seconds?: number | null;
  sector_1?: string | null;
  sector_2?: string | null;
  sector_3?: string | null;
  tyre_compound?: string | null;
  tyre_life?: number | null;
  is_personal_best?: boolean;
}

export interface FastF1DriverComparison {
  drivers: string[];
  fastest_laps: Record<string, FastF1FastestLap>;
  telemetry_delta: Record<
    string,
    {
      delta: number;
      faster: string;
    }
  >;
}
