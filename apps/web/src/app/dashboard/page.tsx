'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SessionSelector from '@/components/dashboard/SessionSelector';
import DriverCard from '@/components/dashboard/DriverCard';
import TelemetryChart from '@/components/charts/TelemetryChart';
import Leaderboard from '@/components/dashboard/Leaderboard';

interface Driver {
  driver_number: number;
  name_acronym: string;
  first_name: string;
  last_name: string;
  team_name: string;
  team_colour: string;
  country_code: string;
}

interface CarData {
  speed: number;
  throttle: number;
  brake: number;
  gear: number;
  rpm: number;
  drs: number;
  date: string;
  driver_number: number;
}

interface Position {
  position: number;
  date: string;
  driver_number: number;
}

export default function DashboardPage() {
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [telemetryData, setTelemetryData] = useState<Map<number, CarData[]>>(new Map());
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch drivers when session changes
  useEffect(() => {
    if (selectedSession) {
      fetchDrivers();
      startTelemetryPolling();
    }
  }, [selectedSession]);

  const fetchDrivers = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/telemetry/drivers?session_key=${selectedSession}`);
      const data = await response.json();
      setDrivers(data);
      // Select first 3 drivers by default
      setSelectedDrivers(data.slice(0, 3).map((d: Driver) => d.driver_number));
    } catch (error) {
      console.error('Failed to fetch drivers:', error);
    }
  };

  const startTelemetryPolling = () => {
    const interval = setInterval(async () => {
      if (!selectedSession || selectedDrivers.length === 0) return;

      try {
        const promises = selectedDrivers.map(async (driverNumber) => {
          const response = await fetch(
            `http://localhost:8000/api/telemetry/car-data?session_key=${selectedSession}&driver_number=${driverNumber}&limit=50`
          );
          const data = await response.json();
          return { driverNumber, data };
        });

        const results = await Promise.all(promises);
        const newTelemetryMap = new Map<number, CarData[]>();
        results.forEach(({ driverNumber, data }) => {
          newTelemetryMap.set(driverNumber, data);
        });
        setTelemetryData(newTelemetryMap);
      } catch (error) {
        console.error('Failed to fetch telemetry:', error);
      }
    }, 1000); // Poll every second

    return () => clearInterval(interval);
  };

  const fetchPositions = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/telemetry/positions?session_key=${selectedSession}&latest=true`
      );
      const data = await response.json();
      setPositions(data);
    } catch (error) {
      console.error('Failed to fetch positions:', error);
    }
  };

  const handleSessionSelect = (sessionKey: number) => {
    setSelectedSession(sessionKey);
  };

  const handleDriverToggle = (driverNumber: number) => {
    setSelectedDrivers((prev) =>
      prev.includes(driverNumber)
        ? prev.filter((d) => d !== driverNumber)
        : [...prev, driverNumber]
    );
  };

  return (
    <Layout>
      <div className="p-6">
        {/* Session Selector */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6"
        >
          <SessionSelector onSelect={handleSessionSelect} />
        </motion.div>

        {isLoading && (
          <div className="flex h-64 items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="h-12 w-12 rounded-full border-4 border-f1-red border-t-transparent"
            />
          </div>
        )}

        {selectedSession && !isLoading && (
          <>
            {/* Driver Cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mb-6"
            >
              <h2 className="mb-4 text-xl font-semibold text-white">Drivers</h2>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-5">
                {drivers.map((driver, index) => (
                  <motion.div
                    key={driver.driver_number}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <DriverCard
                      driver={driver}
                      isSelected={selectedDrivers.includes(driver.driver_number)}
                      onToggle={() => handleDriverToggle(driver.driver_number)}
                    />
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Telemetry Charts */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2"
            >
              <TelemetryChart
                title="Speed (km/h)"
                data={telemetryData}
                dataKey="speed"
                color="#e10600"
                selectedDrivers={selectedDrivers}
                drivers={drivers}
              />
              <TelemetryChart
                title="Throttle (%)"
                data={telemetryData}
                dataKey="throttle"
                color="#00d2be"
                selectedDrivers={selectedDrivers}
                drivers={drivers}
              />
              <TelemetryChart
                title="Brake"
                data={telemetryData}
                dataKey="brake"
                color="#ff8700"
                selectedDrivers={selectedDrivers}
                drivers={drivers}
              />
              <TelemetryChart
                title="RPM"
                data={telemetryData}
                dataKey="rpm"
                color="#871aff"
                selectedDrivers={selectedDrivers}
                drivers={drivers}
              />
            </motion.div>

            {/* Leaderboard */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Leaderboard positions={positions} drivers={drivers} />
            </motion.div>
          </>
        )}

        {!selectedSession && !isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex h-96 flex-col items-center justify-center text-gray-400"
          >
            <svg
              className="mb-4 h-24 w-24 text-gray-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <p className="text-xl">Select a session to view telemetry data</p>
          </motion.div>
        )}
      </div>
    </Layout>
  );
}
