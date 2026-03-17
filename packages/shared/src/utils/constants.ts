// F1 Team identifiers
export const TEAMS = {
  RED_BULL: 'Red Bull Racing',
  FERRARI: 'Ferrari',
  MERCEDES: 'Mercedes',
  MCLAREN: 'McLaren',
  ASTON_MARTIN: 'Aston Martin',
  ALPINE: 'Alpine',
  WILLIAMS: 'Williams',
  ALPHA_TAURI: 'AlphaTauri',
  ALFA_ROMEO: 'Alfa Romeo',
  HAAS: 'Haas F1 Team',
  RB: 'RB',
  KICK_SAUBER: 'Kick Sauber',
} as const;

// Tyre compounds
export const TYRE_COMPOUNDS = {
  SOFT: 'SOFT',
  MEDIUM: 'MEDIUM',
  HARD: 'HARD',
  INTERMEDIATE: 'INTERMEDIATE',
  WET: 'WET',
} as const;

// Session types
export const SESSION_TYPES = {
  PRACTICE_1: 'Practice 1',
  PRACTICE_2: 'Practice 2',
  PRACTICE_3: 'Practice 3',
  QUALIFYING: 'Qualifying',
  SPRINT: 'Sprint',
  RACE: 'Race',
} as const;

// WebSocket message types
export const WS_MESSAGE_TYPES = {
  TELEMETRY: 'telemetry',
  POSITIONS: 'positions',
  TIMING: 'timing',
  WEATHER: 'weather',
  PIT_STOP: 'pit_stop',
  TRACK_STATUS: 'track_status',
} as const;

// API endpoints
export const API_ENDPOINTS = {
  TELEMETRY: '/api/telemetry',
  SESSIONS: '/api/sessions',
  PREDICTIONS: '/api/predictions',
  WEBSOCKET: '/ws',
} as const;
