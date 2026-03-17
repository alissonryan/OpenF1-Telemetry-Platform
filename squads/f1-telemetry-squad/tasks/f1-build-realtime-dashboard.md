# Task: Build Real-Time Dashboard

## Metadata
- **Agent**: @f1-frontend-dev
- **Sprint**: 3-4
- **Priority**: HIGH
- **Estimate**: 16h

## Objective
Criar o dashboard principal com visualização em tempo real de dados de telemetria, posições e informações da corrida.

## Prerequisites
- [ ] Frontend Next.js scaffolded
- [ ] Backend APIs funcionando
- [ ] WebSocket endpoint ativo

## Inputs
- Design specs (se houver)
- API endpoints documentados

## Outputs
- [ ] Dashboard page com layout responsivo
- [ ] Driver cards animados
- [ ] Timing board
- [ ] Track map básico
- [ ] Conexão WebSocket funcionando

## Implementation

### Page Structure
```tsx
// app/dashboard/[session]/page.tsx
import { LiveDashboard } from '@/components/dashboard/live-dashboard';

export default function DashboardPage({ 
  params 
}: { 
  params: { session: string } 
}) {
  return <LiveDashboard sessionKey={parseInt(params.session)} />;
}
```

### Live Dashboard Component
```tsx
// components/dashboard/live-dashboard.tsx
'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useWebSocket } from '@/hooks/use-websocket';
import { useTelemetryStore } from '@/stores/telemetry-store';
import { DriverCard } from './driver-card';
import { TimingBoard } from './timing-board';
import { TrackMap } from '@/components/charts/track-map';
import { WeatherWidget } from './weather-widget';

interface Props {
  sessionKey: number;
}

export function LiveDashboard({ sessionKey }: Props) {
  const { status, data } = useWebSocket(`/ws/telemetry/${sessionKey}`);
  const { drivers, positions, weather } = useTelemetryStore();
  
  return (
    <div className="grid grid-cols-12 gap-4 p-4 min-h-screen bg-slate-900">
      {/* Header */}
      <header className="col-span-12 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white">F1 Live Dashboard</h1>
        <div className="flex items-center gap-4">
          <ConnectionStatus status={status} />
          <WeatherWidget data={weather} />
        </div>
      </header>
      
      {/* Timing Board - Left Sidebar */}
      <aside className="col-span-12 lg:col-span-3">
        <TimingBoard 
          positions={positions} 
          drivers={drivers}
        />
      </aside>
      
      {/* Main Content */}
      <main className="col-span-12 lg:col-span-6 space-y-4">
        {/* Track Map */}
        <motion.div 
          className="bg-slate-800 rounded-lg p-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <TrackMap positions={positions} />
        </motion.div>
        
        {/* Driver Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <AnimatePresence mode="popLayout">
            {drivers.map((driver, index) => (
              <motion.div
                key={driver.number}
                layout
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ delay: index * 0.05 }}
              >
                <DriverCard 
                  driver={driver} 
                  position={positions[driver.number]}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </main>
      
      {/* Telemetry Charts - Right Sidebar */}
      <aside className="col-span-12 lg:col-span-3 space-y-4">
        <SpeedChart data={data} />
        <ThrottleChart data={data} />
        <BrakeChart data={data} />
      </aside>
    </div>
  );
}
```

### WebSocket Hook
```tsx
// hooks/use-websocket.ts
import { useEffect, useRef, useState } from 'react';

type Status = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketReturn {
  status: Status;
  data: any;
  send: (data: any) => void;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [status, setStatus] = useState<Status>('connecting');
  const [data, setData] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}${url}`);
    wsRef.current = ws;
    
    ws.onopen = () => setStatus('connected');
    ws.onclose = () => setStatus('disconnected');
    ws.onerror = () => setStatus('error');
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);
      
      // Update store based on message type
      if (message.type === 'positions') {
        useTelemetryStore.getState().updatePositions(message.data);
      }
    };
    
    return () => ws.close();
  }, [url]);
  
  const send = (data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  };
  
  return { status, data, send };
}
```

### Telemetry Store
```tsx
// stores/telemetry-store.ts
import { create } from 'zustand';

interface Driver {
  number: number;
  code: string;
  name: string;
  team: string;
  color: string;
}

interface Position {
  position: number;
  gap: string;
  lapTime: string;
  sectors: [string, string, string];
}

interface TelemetryState {
  drivers: Driver[];
  positions: Record<number, Position>;
  weather: WeatherData | null;
  selectedDriver: number | null;
  
  setDrivers: (drivers: Driver[]) => void;
  updatePositions: (positions: Record<number, Position>) => void;
  setWeather: (weather: WeatherData) => void;
  selectDriver: (driverNumber: number | null) => void;
}

export const useTelemetryStore = create<TelemetryState>((set) => ({
  drivers: [],
  positions: {},
  weather: null,
  selectedDriver: null,
  
  setDrivers: (drivers) => set({ drivers }),
  updatePositions: (positions) => set({ positions }),
  setWeather: (weather) => set({ weather }),
  selectDriver: (driverNumber) => set({ selectedDriver: driverNumber }),
}));
```

### Driver Card Component
```tsx
// components/dashboard/driver-card.tsx
'use client';

import { motion } from 'framer-motion';
import { Driver, Position } from '@/types';

interface Props {
  driver: Driver;
  position: Position;
}

export function DriverCard({ driver, position }: Props) {
  return (
    <motion.div
      className="relative bg-slate-800 rounded-lg overflow-hidden cursor-pointer
                 hover:ring-2 hover:ring-white/20 transition-shadow"
      style={{ 
        borderLeft: `4px solid ${driver.color}`,
      }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Position Badge */}
      <motion.div
        className="absolute top-2 left-2 w-8 h-8 rounded-full bg-white/10 
                   flex items-center justify-center font-bold text-white"
        key={position.position}
        initial={{ scale: 1.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        {position.position}
      </motion.div>
      
      {/* Driver Info */}
      <div className="p-4 pt-12">
        <div className="font-mono text-lg font-bold text-white">
          {driver.code}
        </div>
        <div className="text-sm text-slate-400 truncate">
          {driver.name}
        </div>
        
        {/* Gap */}
        <div className="mt-2 text-xs text-slate-300">
          {position.gap || 'LEADER'}
        </div>
        
        {/* Last Lap */}
        <div className="mt-1 font-mono text-sm text-emerald-400">
          {position.lapTime}
        </div>
      </div>
    </motion.div>
  );
}
```

### Timing Board
```tsx
// components/dashboard/timing-board.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Driver, Position } from '@/types';

interface Props {
  drivers: Driver[];
  positions: Record<number, Position>;
}

export function TimingBoard({ drivers, positions }: Props) {
  // Sort by position
  const sortedDrivers = [...drivers].sort(
    (a, b) => (positions[a.number]?.position || 99) - 
              (positions[b.number]?.position || 99)
  );
  
  return (
    <div className="bg-slate-800 rounded-lg p-4 h-full overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-4">Live Timing</h2>
      
      <div className="space-y-2">
        <AnimatePresence mode="popLayout">
          {sortedDrivers.map((driver, index) => (
            <motion.div
              key={driver.number}
              layout
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.02 }}
              className="flex items-center gap-3 p-2 rounded bg-slate-700/50"
              style={{ borderLeft: `3px solid ${driver.color}` }}
            >
              {/* Position */}
              <span className="w-6 text-center font-bold text-white">
                {positions[driver.number]?.position}
              </span>
              
              {/* Driver Code */}
              <span className="font-mono text-white w-8">
                {driver.code}
              </span>
              
              {/* Gap */}
              <span className="text-sm text-slate-300 flex-1 text-right">
                {positions[driver.number]?.gap || '—'}
              </span>
              
              {/* Last Lap */}
              <span className="font-mono text-sm text-emerald-400 w-16 text-right">
                {positions[driver.number]?.lapTime}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
```

## Acceptance Criteria
- [ ] Dashboard carrega e mostra dados
- [ ] WebSocket conecta automaticamente
- [ ] Positions atualizam em tempo real
- [ ] Animações são fluidas (60fps)
- [ ] Layout responsivo funciona em mobile
- [ ] Estado de conexão é visível

## Performance Targets
- First Paint: < 1s
- Time to Interactive: < 3s
- WebSocket latency: < 100ms
- Animation frame rate: 60fps

## Dependencies
- f1-setup-project
- f1-connect-openf1

## Risks
- Performance com muitos drivers atualizando
- Memory leaks com WebSocket
