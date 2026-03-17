'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { motion } from 'framer-motion';

interface TelemetryChartProps {
  title: string;
  data: Map<number, any[]>;
  dataKey: string;
  color: string;
  selectedDrivers: number[];
  drivers: any[];
}

const DRIVER_COLORS = [
  '#e10600', // F1 Red
  '#00d2be', // Mercedes
  '#ff8700', // McLaren
  '#0600ef', // Red Bull
  '#006f62', // Aston Martin
  '#2b4562', // Alpha Tauri
  '#b6babd', // Alfa Romeo
  '#f58020', // Haas
  '#2e8b57', // Williams
  '#ff69b4', // Pink
];

export default function TelemetryChart({
  title,
  data,
  dataKey,
  color,
  selectedDrivers,
  drivers,
}: TelemetryChartProps) {
  // Combine data from all selected drivers
  const chartData = useMemo(() => {
    if (selectedDrivers.length === 0) return [];

    // Get all data points from all drivers
    const allPoints: any[] = [];
    selectedDrivers.forEach((driverNumber) => {
      const driverData = data.get(driverNumber) || [];
      driverData.forEach((point) => {
        allPoints.push({
          ...point,
          driverNumber,
          time: new Date(point.date).getTime(),
        });
      });
    });

    // Sort by time
    allPoints.sort((a, b) => a.time - b.time);

    // Group by time buckets (100ms intervals)
    const timeBuckets = new Map<number, any>();
    allPoints.forEach((point) => {
      const bucketTime = Math.floor(point.time / 100) * 100;
      const existing = timeBuckets.get(bucketTime) || { time: bucketTime };
      existing[`driver_${point.driverNumber}`] = point[dataKey];
      timeBuckets.set(bucketTime, existing);
    });

    return Array.from(timeBuckets.values())
      .sort((a, b) => a.time - b.time)
      .slice(-50); // Last 50 data points
  }, [data, selectedDrivers, dataKey]);

  const getDriverColor = (driverNumber: number) => {
    const driver = drivers.find((d) => d.driver_number === driverNumber);
    if (driver?.team_colour) {
      return `#${driver.team_colour}`;
    }
    const index = selectedDrivers.indexOf(driverNumber);
    return DRIVER_COLORS[index % DRIVER_COLORS.length];
  };

  const getDriverName = (driverNumber: number) => {
    const driver = drivers.find((d) => d.driver_number === driverNumber);
    return driver?.name_acronym || `Driver ${driverNumber}`;
  };

  if (selectedDrivers.length === 0) {
    return (
      <div className="rounded-lg bg-gray-800/50 p-6 backdrop-blur">
        <h3 className="mb-4 text-lg font-semibold text-white">{title}</h3>
        <div className="flex h-64 items-center justify-center text-gray-500">
          Select drivers to view telemetry
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="rounded-lg bg-gray-800/50 p-6 backdrop-blur"
    >
      <h3 className="mb-4 text-lg font-semibold text-white">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="time"
              tick={false}
              stroke="#9ca3af"
            />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            {selectedDrivers.map((driverNumber) => (
              <Line
                key={driverNumber}
                type="monotone"
                dataKey={`driver_${driverNumber}`}
                name={getDriverName(driverNumber)}
                stroke={getDriverColor(driverNumber)}
                strokeWidth={2}
                dot={false}
                animationDuration={300}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
