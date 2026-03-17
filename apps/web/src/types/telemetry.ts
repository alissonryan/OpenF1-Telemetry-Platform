export interface TelemetryData {
  date: string;
  session_key: number;
  meeting_key: number;
  driver_number: number;
  speed: number;
  throttle: number;
  brake: number;
  drs: number;
  n_gear: number;
  rpm: number;
}

export interface PositionData {
  date: string;
  session_key: number;
  meeting_key: number;
  driver_number: number;
  position: number;
  x: number;
  y: number;
  z: number;
}

export interface LapData {
  session_key: number;
  meeting_key: number;
  driver_number: number;
  i1_speed?: number;
  i2_speed?: number;
  st_speed?: number;
  lap_number: number;
  lap_duration?: number;
  is_pit_out_lap?: boolean;
  date_start: string;
}

export interface Driver {
  driver_number: number;
  broadcast_name: string;
  full_name: string;
  name_acronym: string;
  team_name: string;
  team_colour: string;
  country_code: string;
  headshot_url?: string;
}
