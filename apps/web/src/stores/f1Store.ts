import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Session {
  meeting_key: number;
  session_key: number;
  session_name: string;
  session_type: string;
  circuit_short_name: string;
  country_name: string;
  date_start: string;
  date_end: string;
}

export interface Driver {
  driver_number: number;
  name_acronym?: string;
  first_name?: string;
  last_name?: string;
  team_name?: string;
  team_colour?: string;
  country_code?: string;
}

import type { TelemetryData, PositionData } from '@/hooks/useWebSocket';

interface F1State {
  // Session state
  selectedSessionKey: number | null;
  selectedMeetingKey: number | null;
  sessions: Session[];
  session: Session | null;

  // Driver state
  drivers: Driver[];
  selectedDrivers: number[];

  // Telemetry state
  telemetryData: Map<number, TelemetryData[]>;
  positions: PositionData[];
  laps: Record<string, unknown>[];

  // UI state
  isLoading: boolean;
  error: string | null;

  // Actions
  setSelectedSession: (sessionKey: number | null) => void;
  setSelectedMeeting: (meetingKey: number | null) => void;
  setSessions: (sessions: Session[]) => void;
  setSession: (session: Session | null) => void;
  setDrivers: (drivers: Driver[]) => void;
  setSelectedDrivers: (driverNumbers: number[]) => void;
  toggleDriver: (driverNumber: number) => void;
  setTelemetryData: (data: Map<number, TelemetryData[]>) => void;
  setPositions: (positions: PositionData[]) => void;
  setLaps: (laps: Record<string, unknown>[]) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  selectedSessionKey: null,
  selectedMeetingKey: null,
  sessions: [],
  session: null,
  drivers: [],
  selectedDrivers: [],
  telemetryData: new Map(),
  positions: [],
  laps: [],
  isLoading: false,
  error: null,
};

export const useF1Store = create<F1State>()(
  persist(
    (set) => ({
      ...initialState,

      setSelectedSession: (sessionKey) =>
        set({ selectedSessionKey: sessionKey }),

      setSelectedMeeting: (meetingKey) =>
        set({ selectedMeetingKey: meetingKey }),

      setSessions: (sessions) => set({ sessions }),

      setSession: (session) => set({ session }),

      setDrivers: (drivers) => set({ drivers }),

      setSelectedDrivers: (driverNumbers) =>
        set({ selectedDrivers: driverNumbers }),

      toggleDriver: (driverNumber) =>
        set((state) => ({
          selectedDrivers: state.selectedDrivers.includes(driverNumber)
            ? state.selectedDrivers.filter((d) => d !== driverNumber)
            : [...state.selectedDrivers, driverNumber],
        })),

      setTelemetryData: (data) => set({ telemetryData: data }),

      setPositions: (positions) => set({ positions }),

      setLaps: (laps) => set({ laps }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      reset: () => set(initialState),
    }),
    {
      name: 'f1-storage',
      partialize: (state) => ({
        selectedSessionKey: state.selectedSessionKey,
        selectedMeetingKey: state.selectedMeetingKey,
        selectedDrivers: state.selectedDrivers,
      }),
    }
  )
);
