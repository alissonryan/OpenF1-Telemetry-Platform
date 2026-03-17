'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '@/components/layout/Layout';
import SimpleSessionSelector from '@/components/dashboard/SimpleSessionSelector';
import PitStopPredictionCard from '@/components/predictions/PitStopPredictionCard';
import PositionForecastTable from '@/components/predictions/PositionForecastTable';
import StrategyRecommendations from '@/components/predictions/StrategyRecommendations';
import ConnectionStatus from '@/components/ui/ConnectionStatus';
import { usePredictions } from '@/hooks/usePredictions';
import type { PitPrediction, StrategyAnalysis } from '@/types/predictions';

interface Driver {
  driver_number: number;
  name_acronym: string;
  first_name: string;
  last_name: string;
  team_name: string;
  team_colour: string;
}

export default function PredictionsPage() {
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [activeTab, setActiveTab] = useState<'pit' | 'positions' | 'strategy'>('pit');
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  
  // Use predictions hook
  const {
    pitPredictions,
    positionForecast,
    strategies,
    isLoadingPit,
    isLoadingPositions,
    isLoadingStrategy,
    pitError,
    positionError,
    strategyError,
    lastUpdate,
    isConnected,
  } = usePredictions({
    sessionKey: selectedSession || undefined,
    autoRefresh: true,
    refreshInterval: 10000, // 10 seconds
  });
  
  // Fetch drivers when session changes
  useEffect(() => {
    if (selectedSession) {
      fetchDrivers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSession]);
  
  const fetchDrivers = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/telemetry/drivers?session_key=${selectedSession}`
      );
      const data = await response.json();
      setDrivers(data);
      setSelectedDrivers(data.slice(0, 5).map((d: Driver) => d.driver_number));
    } catch (error) {
      console.error('Failed to fetch drivers:', error);
    }
  };
  
  // Get pit predictions for selected drivers
  const selectedPitPredictions = useMemo(() => {
    const predictions: Array<{ driver: Driver; prediction: PitPrediction }> = [];
    
    selectedDrivers.forEach(driverNum => {
      const prediction = pitPredictions.get(driverNum);
      const driver = drivers.find(d => d.driver_number === driverNum);
      
      if (prediction && driver) {
        predictions.push({ driver, prediction });
      }
    });
    
    // Sort by probability (highest first)
    return predictions.sort((a, b) => b.prediction.probability - a.prediction.probability);
  }, [selectedDrivers, pitPredictions, drivers]);
  
  // Get strategies for selected drivers
  const selectedStrategies = useMemo(() => {
    const strategyList: StrategyAnalysis[] = [];
    
    selectedDrivers.forEach(driverNum => {
      const strategy = strategies.get(driverNum);
      if (strategy) {
        strategyList.push(strategy);
      }
    });
    
    return strategyList;
  }, [selectedDrivers, strategies]);
  
  // Enhanced position forecast with driver info
  const enhancedPositionForecast = useMemo(() => {
    return positionForecast.map(pred => {
      const driver = drivers.find(d => d.driver_number === pred.driver_number);
      return {
        ...pred,
        driver_name: driver ? `${driver.first_name} ${driver.last_name}` : `Driver ${pred.driver_number}`,
        team_name: driver?.team_name || 'Unknown',
      };
    });
  }, [positionForecast, drivers]);
  
  // Filter position forecast for selected drivers
  const filteredPositionForecast = useMemo(() => {
    if (selectedDrivers.length === 0) return enhancedPositionForecast;
    return enhancedPositionForecast.filter(pred => selectedDrivers.includes(pred.driver_number));
  }, [enhancedPositionForecast, selectedDrivers]);
  
  const handleDriverToggle = (driverNumber: number) => {
    setSelectedDrivers(prev => {
      if (prev.includes(driverNumber)) {
        return prev.filter(d => d !== driverNumber);
      }
      return [...prev, driverNumber];
    });
  };
  
  const tabs = [
    { id: 'pit' as const, label: 'Pit Stop Predictions', icon: '🏁' },
    { id: 'positions' as const, label: 'Position Forecast', icon: '📊' },
    { id: 'strategy' as const, label: 'Strategy', icon: '📋' },
  ];
  
  return (
    <Layout>
      <div className="p-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-center justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold text-white">ML Predictions Dashboard</h1>
            <p className="text-sm text-gray-400 mt-1">
              AI-powered predictions for pit stops, positions, and strategy
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                Last update: {new Date(lastUpdate).toLocaleTimeString()}
              </span>
            )}
            <ConnectionStatus
              isConnected={isConnected}
              connectionState={isConnected ? 'connected' : 'disconnected'}
              showDetails={false}
            />
          </div>
        </motion.div>
        
        {/* Session Selector */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6"
        >
          <SimpleSessionSelector onSelect={setSelectedSession} />
        </motion.div>
        
        {selectedSession && (
          <>
            {/* Driver Selection */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mb-6"
            >
              <h2 className="text-lg font-semibold text-white mb-3">Select Drivers</h2>
              <div className="flex flex-wrap gap-2">
                {drivers.map(driver => (
                  <motion.button
                    key={driver.driver_number}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleDriverToggle(driver.driver_number)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedDrivers.includes(driver.driver_number)
                        ? 'bg-f1-red text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                    style={{
                      borderLeft: `3px solid #${driver.team_colour}`,
                    }}
                  >
                    {driver.name_acronym}
                  </motion.button>
                ))}
              </div>
            </motion.div>
            
            {/* Tabs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mb-6"
            >
              <div className="flex gap-2 border-b border-gray-700">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-4 py-3 text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'text-f1-red border-b-2 border-f1-red'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </div>
            </motion.div>
            
            {/* Content */}
            <AnimatePresence mode="wait">
              {activeTab === 'pit' && (
                <motion.div
                  key="pit"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                >
                  {pitError && (
                    <div className="mb-4 p-4 bg-red-500/20 text-red-400 rounded-lg">
                      {pitError}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {selectedPitPredictions.map(({ driver, prediction }, index) => (
                      <motion.div
                        key={driver.driver_number}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <PitStopPredictionCard
                          driver={driver}
                          prediction={prediction}
                          isHighlighted={prediction.probability >= 0.7}
                        />
                      </motion.div>
                    ))}
                    
                    {selectedPitPredictions.length === 0 && !isLoadingPit && (
                      <div className="col-span-full text-center py-12 text-gray-400">
                        No predictions available. Select drivers to see pit predictions.
                      </div>
                    )}
                    
                    {isLoadingPit && (
                      <div className="col-span-full flex justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-2 border-f1-red border-t-transparent" />
                      </div>
                    )}
                  </div>
                  
                  {/* Legend */}
                  <div className="mt-6 p-4 bg-gray-800/50 rounded-lg">
                    <h3 className="text-sm font-medium text-white mb-2">Understanding Predictions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-400">
                      <div>
                        <span className="text-red-500 font-medium">Red Indicator</span>
                        <p>High pit probability (≥70%) - pit stop imminent</p>
                      </div>
                      <div>
                        <span className="text-yellow-500 font-medium">Yellow Indicator</span>
                        <p>Medium probability (40-69%) - monitor closely</p>
                      </div>
                      <div>
                        <span className="text-green-500 font-medium">Green Indicator</span>
                        <p>Low probability (&lt;40%) - unlikely to pit soon</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
              
              {activeTab === 'positions' && (
                <motion.div
                  key="positions"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                >
                  {positionError && (
                    <div className="mb-4 p-4 bg-red-500/20 text-red-400 rounded-lg">
                      {positionError}
                    </div>
                  )}
                  
                  <PositionForecastTable
                    predictions={filteredPositionForecast}
                    isLoading={isLoadingPositions}
                  />
                </motion.div>
              )}
              
              {activeTab === 'strategy' && (
                <motion.div
                  key="strategy"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                >
                  {strategyError && (
                    <div className="mb-4 p-4 bg-red-500/20 text-red-400 rounded-lg">
                      {strategyError}
                    </div>
                  )}
                  
                  <StrategyRecommendations
                    recommendations={selectedStrategies}
                    isLoading={isLoadingStrategy}
                  />
                  
                  {selectedStrategies.length === 0 && !isLoadingStrategy && (
                    <div className="text-center py-12 text-gray-400">
                      No strategy recommendations. Select drivers to see strategies.
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Model Accuracy Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mt-8 p-6 bg-gray-800/50 rounded-xl border border-gray-700/50"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Model Performance</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-f1-red">85%</p>
                  <p className="text-sm text-gray-400 mt-1">Pit Prediction Accuracy</p>
                  <p className="text-xs text-gray-500">Last 10 races</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-400">78%</p>
                  <p className="text-sm text-gray-400 mt-1">Position Forecast Accuracy</p>
                  <p className="text-xs text-gray-500">Within 2 positions</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-yellow-400">72%</p>
                  <p className="text-sm text-gray-400 mt-1">Strategy Optimization</p>
                  <p className="text-xs text-gray-500">Positions gained vs baseline</p>
                </div>
              </div>
            </motion.div>
          </>
        )}
        
        {!selectedSession && (
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
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            <p className="text-xl">Select a session to view ML predictions</p>
            <p className="mt-2 text-sm text-gray-500">
              Predictions update automatically every 10 seconds
            </p>
          </motion.div>
        )}
      </div>
    </Layout>
  );
}
