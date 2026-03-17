export interface F1DbDriver {
  id: string;
  name: string;
  first_name: string;
  last_name: string;
  full_name: string;
  abbreviation: string;
  permanent_number?: string | null;
  gender: string;
  date_of_birth: string;
  date_of_death?: string | null;
  place_of_birth: string;
  country_of_birth_id: string;
  nationality_country_id: string;
}

export interface F1DbDriverStatistics {
  driver_id: string;
  best_championship_position?: number | null;
  best_starting_grid_position?: number | null;
  best_race_result?: number | null;
  best_sprint_race_result?: number | null;
  total_championship_wins: number;
  total_race_entries: number;
  total_race_starts: number;
  total_race_wins: number;
  total_race_laps: number;
  total_podiums: number;
  total_points: number;
  total_championship_points: number;
  total_pole_positions: number;
  total_fastest_laps: number;
  total_sprint_race_starts: number;
  total_sprint_race_wins: number;
  total_driver_of_the_day: number;
  total_grand_slams: number;
}

export interface F1DbCircuit {
  id: string;
  name: string;
  full_name: string;
  previous_names?: string | null;
  type: string;
  direction: string;
  place_name: string;
  country_id: string;
  latitude: number;
  longitude: number;
  length: number;
  turns: number;
  total_races_held: number;
}

export interface F1DbRace {
  id: number;
  year: number;
  round: number;
  date: string;
  round_number?: number;
  race_date?: string;
  time?: string | null;
  grand_prix_id: string;
  official_name: string;
  qualifying_format: string;
  circuit_id: string;
  circuit_type: string;
  direction: string;
  course_length: number;
  turns: number;
  laps: number;
  distance: number;
}

export interface F1DbRaceResult {
  race_id: number;
  position_display_order: number;
  position_number?: number | null;
  position_text: string;
  driver_number?: number | null;
  driver_id: string;
  constructor_id: string;
  laps?: number | null;
  time?: string | null;
  gap?: string | null;
  interval?: string | null;
  points?: number | null;
  grid_position_number?: number | null;
  positions_gained?: number | null;
  pit_stops?: number | null;
  fastest_lap?: boolean | null;
}

export interface F1DbDriverStanding {
  year: number;
  position_display_order: number;
  position_number?: number | null;
  position_text: string;
  driver_id: string;
  points: number;
  championship_won: boolean;
}

export interface F1DbConstructorStanding {
  year: number;
  position_display_order: number;
  position_number?: number | null;
  position_text: string;
  constructor_id: string;
  points: number;
  championship_won: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ListResponse<T> {
  data: T[];
  total: number;
}
