export interface Session {
  session_key: number;
  meeting_key: number;
  location: string;
  session_type: 'practice' | 'qualifying' | 'sprint' | 'race';
  session_name: string;
  date_start: string;
  date_end: string;
  country_name: string;
  circuit_short_name: string;
  year: number;
}

export interface Meeting {
  meeting_key: number;
  meeting_name: string;
  location: string;
  official_name: string;
  country_key: number;
  country_name: string;
  circuit_key: number;
  circuit_short_name: string;
  date_start: string;
  date_end: string;
  year: number;
}
