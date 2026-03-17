'use client';

import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import {
  TrackData,
  TRACKS,
  getTrackByKey,
  getTrackByName,
  getPositionOnTrack,
  getSectorForProgress,
  isInDRSZone,
  DEFAULT_TRACK,
} from '@/lib/trackData';

// ==================== Types ====================

export interface DriverPosition {
  driver_number: number;
  x: number;
  y: number;
  z?: number;
  position: number;
  speed?: number;
  lap?: number;
  gap?: string;
  drs?: number;
  date: string;
}

export interface DriverInfo {
  driver_number: number;
  name_acronym: string;
  first_name?: string;
  last_name?: string;
  team_name: string;
  team_colour: string;
}

export interface MiniSectorData {
  startPercent: number;
  endPercent: number;
  speed: number; // 0-100, relative speed
  color: string;
}

export interface IncidentMarker {
  type: 'yellow' | 'red' | 'sc' | 'vsc';
  position: number; // percentage along track
  label?: string;
}

interface TrackMapProps {
  track?: TrackData | null;
  circuitKey?: number;
  circuitName?: string;
  positions: DriverPosition[];
  drivers: DriverInfo[];
  selectedDrivers?: number[];
  onDriverClick?: (driverNumber: number) => void;
  onDriverHover?: (driverNumber: number | null) => void;
  miniSectors?: MiniSectorData[];
  incidents?: IncidentMarker[];
  showDRSZones?: boolean;
  showSectors?: boolean;
  showSpeedGradient?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

// ==================== Constants ====================

const TEAM_COLORS: Record<string, string> = {
  'Mercedes': '#00D2BE',
  'Red Bull Racing': '#0600EF',
  'Ferrari': '#DC0000',
  'McLaren': '#FF8700',
  'Aston Martin': '#006F62',
  'Alpine': '#0090FF',
  'Williams': '#005AFF',
  'AlphaTauri': '#2B4562',
  'Alfa Romeo': '#900000',
  'Haas F1 Team': '#FFFFFF',
  'RB': '#6692FF',
  'Kick Sauber': '#52E252',
  'Sauber': '#52E252',
};

const SECTOR_COLORS = ['#00d2be', '#ff8700', '#e10600'];
const SPEED_COLORS = {
  slow: '#ef4444',     // red
  medium: '#f59e0b',   // amber
  fast: '#22c55e',     // green
  fastest: '#8b5cf6',  // purple
};

const SIZE_CONFIG = {
  sm: { width: 280, height: 280, fontSize: 10, dotSize: 12 },
  md: { width: 400, height: 400, fontSize: 12, dotSize: 16 },
  lg: { width: 550, height: 550, fontSize: 14, dotSize: 20 },
};

// ==================== Helper Functions ====================

function getDriverColor(driver: DriverInfo): string {
  if (driver.team_colour) {
    return `#${driver.team_colour}`;
  }
  return TEAM_COLORS[driver.team_name] || '#666666';
}

function interpolateSpeedColor(speed: number): string {
  // Speed is 0-100, where 0 is slowest, 100 is fastest
  if (speed >= 90) return SPEED_COLORS.fastest;
  if (speed >= 70) return SPEED_COLORS.fast;
  if (speed >= 50) return SPEED_COLORS.medium;
  return SPEED_COLORS.slow;
}

function normalizePosition(
  x: number,
  y: number,
  viewBoxWidth: number,
  viewBoxHeight: number
): { x: number; y: number } {
  // Assuming input coords are 0-1000 scale
  return {
    x: (x / 1000) * viewBoxWidth,
    y: (y / 1000) * viewBoxHeight,
  };
}

// ==================== Sub-Components ====================

interface DriverDotProps {
  driver: DriverInfo;
  position: DriverPosition;
  color: string;
  isSelected: boolean;
  isHovered: boolean;
  dotSize: number;
  fontSize: number;
  onClick?: () => void;
  onHover?: (hovered: boolean) => void;
}

function DriverDot({
  driver,
  position,
  color,
  isSelected,
  isHovered,
  dotSize,
  fontSize,
  onClick,
  onHover,
}: DriverDotProps) {
  const displayX = position.x;
  const displayY = position.y;

  return (
    <g
      className="cursor-pointer"
      onClick={onClick}
      onMouseEnter={() => onHover?.(true)}
      onMouseLeave={() => onHover?.(false)}
    >
      {/* Glow effect for selected/hovered */}
      {(isSelected || isHovered) && (
        <motion.circle
          cx={displayX}
          cy={displayY}
          r={dotSize + 6}
          fill={color}
          opacity={0.3}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 0.3 }}
          transition={{ duration: 0.2 }}
        />
      )}
      
      {/* Main dot with Framer Motion animation */}
      <motion.circle
        cx={displayX}
        cy={displayY}
        r={dotSize}
        fill={color}
        stroke={isSelected ? '#ffffff' : 'rgba(255,255,255,0.5)'}
        strokeWidth={isSelected ? 2 : 1}
        initial={{ scale: 0 }}
        animate={{ 
          scale: 1,
          cx: displayX,
          cy: displayY,
        }}
        transition={{ 
          type: 'spring',
          stiffness: 300,
          damping: 25,
        }}
      />

      {/* Driver number */}
      <text
        x={displayX}
        y={displayY + fontSize / 3}
        textAnchor="middle"
        fontSize={fontSize}
        fontWeight="bold"
        fill={color === '#FFFFFF' ? '#000000' : '#ffffff'}
        className="pointer-events-none select-none"
      >
        {driver.driver_number}
      </text>

      {/* DRS indicator */}
      {position.drs === 1 && (
        <motion.circle
          cx={displayX + dotSize + 2}
          cy={displayY - dotSize - 2}
          r={4}
          fill="#00ff00"
          initial={{ scale: 0 }}
          animate={{ scale: [1, 1.3, 1] }}
          transition={{ 
            duration: 0.5, 
            repeat: Infinity,
            repeatType: 'reverse' 
          }}
        />
      )}
    </g>
  );
}

interface DriverTooltipProps {
  driver: DriverInfo;
  position: DriverPosition;
  color: string;
  x: number;
  y: number;
}

function DriverTooltip({ driver, position, color, x, y }: DriverTooltipProps) {
  return (
    <motion.g
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 5 }}
    >
      <rect
        x={x - 60}
        y={y - 70}
        width={120}
        height={60}
        rx={6}
        fill="rgba(15, 23, 42, 0.95)"
        stroke={color}
        strokeWidth={1}
      />
      <text x={x} y={y - 52} textAnchor="middle" fontSize={11} fill="#ffffff" fontWeight="bold">
        {driver.name_acronym} - P{position.position}
      </text>
      {position.speed !== undefined && (
        <text x={x} y={y - 36} textAnchor="middle" fontSize={10} fill="#9ca3af">
          {position.speed} km/h
        </text>
      )}
      {position.gap && (
        <text x={x} y={y - 20} textAnchor="middle" fontSize={10} fill="#9ca3af">
          Gap: {position.gap}
        </text>
      )}
    </motion.g>
  );
}

interface DRSZoneOverlayProps {
  track: TrackData;
  viewBoxWidth: number;
  viewBoxHeight: number;
}

function DRSZoneOverlay({ track, viewBoxWidth, viewBoxHeight }: DRSZoneOverlayProps) {
  if (!track.drs_zones || track.drs_zones.length === 0) return null;

  return (
    <g className="opacity-30">
      {track.drs_zones.map((zone, index) => {
        const startPos = getPositionOnTrack(track, zone.start);
        const endPos = getPositionOnTrack(track, zone.end);
        
        const normalizedStart = normalizePosition(startPos.x, startPos.y, viewBoxWidth, viewBoxHeight);
        const normalizedEnd = normalizePosition(endPos.x, endPos.y, viewBoxWidth, viewBoxHeight);

        return (
          <line
            key={`drs-${index}`}
            x1={normalizedStart.x}
            y1={normalizedStart.y}
            x2={normalizedEnd.x}
            y2={normalizedEnd.y}
            stroke="#00ff00"
            strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray="10,5"
          />
        );
      })}
    </g>
  );
}

interface IncidentFlagProps {
  incident: IncidentMarker;
  track: TrackData;
  viewBoxWidth: number;
  viewBoxHeight: number;
}

function IncidentFlag({ incident, track, viewBoxWidth, viewBoxHeight }: IncidentFlagProps) {
  const pos = getPositionOnTrack(track, incident.position);
  const normalized = normalizePosition(pos.x, pos.y, viewBoxWidth, viewBoxHeight);

  const flagColors: Record<string, string> = {
    yellow: '#fbbf24',
    red: '#ef4444',
    sc: '#f59e0b',
    vsc: '#fcd34d',
  };

  return (
    <g>
      <circle
        cx={normalized.x}
        cy={normalized.y - 20}
        r={8}
        fill={flagColors[incident.type]}
        className="animate-pulse"
      />
      <text
        x={normalized.x}
        y={normalized.y - 16}
        textAnchor="middle"
        fontSize={8}
        fill="#000"
        fontWeight="bold"
      >
        {incident.type.toUpperCase()}
      </text>
    </g>
  );
}

// ==================== Main Component ====================

export default function TrackMap({
  track,
  circuitKey,
  circuitName,
  positions,
  drivers,
  selectedDrivers = [],
  onDriverClick,
  onDriverHover,
  miniSectors,
  incidents = [],
  showDRSZones = true,
  showSectors = true,
  showSpeedGradient = false,
  className,
  size = 'md',
}: TrackMapProps) {
  const [hoveredDriver, setHoveredDriver] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Determine which track to use - always return a valid track (fallback to DEFAULT_TRACK)
  const currentTrack: TrackData = useMemo(() => {
    if (track) return track;
    if (circuitKey) return getTrackByKey(circuitKey) ?? DEFAULT_TRACK;
    if (circuitName) return getTrackByName(circuitName) ?? DEFAULT_TRACK;
    return DEFAULT_TRACK;
  }, [track, circuitKey, circuitName]);

  // Get size configuration
  const sizeConfig = SIZE_CONFIG[size];
  const viewBoxWidth = 1000;
  const viewBoxHeight = 1000;

  // Normalize track coordinates
  const normalizedCoords = useMemo(() => {
    return currentTrack.coordinates.map(coord => 
      normalizePosition(coord.x, coord.y, viewBoxWidth, viewBoxHeight)
    );
  }, [currentTrack]);

  // Create SVG path for the track
  const trackPath = useMemo(() => {
    if (normalizedCoords.length < 2) return '';
    
    let path = `M ${normalizedCoords[0].x} ${normalizedCoords[0].y}`;
    for (let i = 1; i < normalizedCoords.length; i++) {
      path += ` L ${normalizedCoords[i].x} ${normalizedCoords[i].y}`;
    }
    path += ' Z'; // Close the path
    
    return path;
  }, [normalizedCoords]);

  // Create sector paths
  const sectorPaths = useMemo(() => {
    if (!showSectors) return [];
    
    return currentTrack.sectors.map((sector, index) => {
      const sectorCoords = normalizedCoords.slice(sector.start, sector.end + 1);
      if (sectorCoords.length < 2) return null;
      
      let path = `M ${sectorCoords[0].x} ${sectorCoords[0].y}`;
      for (let i = 1; i < sectorCoords.length; i++) {
        path += ` L ${sectorCoords[i].x} ${sectorCoords[i].y}`;
      }
      
      return {
        path,
        color: SECTOR_COLORS[index % SECTOR_COLORS.length],
        index,
      };
    }).filter(Boolean);
  }, [normalizedCoords, currentTrack.sectors, showSectors]);

  // Create mini-sector gradient segments
  const miniSectorPaths = useMemo(() => {
    if (!miniSectors || !showSpeedGradient) return [];
    
    return miniSectors.map((sector, index) => {
      const startPos = getPositionOnTrack(currentTrack, sector.startPercent);
      const endPos = getPositionOnTrack(currentTrack, sector.endPercent);
      
      const normalizedStart = normalizePosition(startPos.x, startPos.y, viewBoxWidth, viewBoxHeight);
      const normalizedEnd = normalizePosition(endPos.x, endPos.y, viewBoxWidth, viewBoxHeight);

      return {
        start: normalizedStart,
        end: normalizedEnd,
        color: interpolateSpeedColor(sector.speed),
        speed: sector.speed,
        index,
      };
    });
  }, [miniSectors, showSpeedGradient, currentTrack]);

  // Get driver info by number
  const getDriverInfo = useCallback(
    (driverNumber: number): DriverInfo | undefined => {
      return drivers.find(d => d.driver_number === driverNumber);
    },
    [drivers]
  );

  // Handle driver hover
  const handleDriverHover = useCallback((driverNumber: number | null) => {
    setHoveredDriver(driverNumber);
    onDriverHover?.(driverNumber);
  }, [onDriverHover]);

  // Handle resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Sort positions by track position (for z-ordering)
  const sortedPositions = useMemo(() => {
    return [...positions].sort((a, b) => {
      const aDriver = getDriverInfo(a.driver_number);
      const bDriver = getDriverInfo(b.driver_number);
      if (!aDriver || !bDriver) return 0;
      return (a.position || 0) - (b.position || 0);
    });
  }, [positions, getDriverInfo]);

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative rounded-lg bg-gray-800/50 backdrop-blur-sm overflow-hidden',
        className
      )}
    >
      {/* Track name header */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
        <span className="text-sm font-semibold text-white">
          {currentTrack.official_name}
        </span>
        <span className="text-xs text-gray-400">
          {currentTrack.country}
        </span>
      </div>

      {/* Legend */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1">
        {showSectors && (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            {['S1', 'S2', 'S3'].map((label, i) => (
              <div key={label} className="flex items-center gap-1">
                <div
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: SECTOR_COLORS[i] }}
                />
                <span>{label}</span>
              </div>
            ))}
          </div>
        )}
        {showDRSZones && currentTrack.drs_zones && currentTrack.drs_zones.length > 0 && (
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <div className="h-2 w-4 rounded bg-green-500 opacity-50" />
            <span>DRS</span>
          </div>
        )}
      </div>

      {/* SVG Track Map */}
      <svg
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        className="w-full h-full"
        style={{ 
          minHeight: sizeConfig.height, 
          maxHeight: sizeConfig.height * 1.5,
        }}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Background grid */}
        <defs>
          <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* Track outline (outer stroke) */}
        <path
          d={trackPath}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={40}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Sector-colored track or single color */}
        {showSectors && sectorPaths.length > 0 ? (
          sectorPaths.map((sector, index) => (
            <motion.path
              key={`sector-${index}`}
              d={sector!.path}
              fill="none"
              stroke={sector!.color}
              strokeWidth={20}
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1, delay: index * 0.2 }}
            />
          ))
        ) : (
          <path
            d={trackPath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth={20}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* Speed gradient overlay */}
        {showSpeedGradient && miniSectorPaths.map((segment) => (
          <line
            key={`speed-${segment.index}`}
            x1={segment.start.x}
            y1={segment.start.y}
            x2={segment.end.x}
            y2={segment.end.y}
            stroke={segment.color}
            strokeWidth={24}
            strokeLinecap="round"
            opacity={0.6}
          />
        ))}

        {/* DRS zones */}
        {showDRSZones && (
          <DRSZoneOverlay
            track={currentTrack}
            viewBoxWidth={viewBoxWidth}
            viewBoxHeight={viewBoxHeight}
          />
        )}

        {/* Start/Finish line */}
        {normalizedCoords.length > 0 && (
          <g>
            <rect
              x={normalizedCoords[0].x - 15}
              y={normalizedCoords[0].y - 3}
              width={30}
              height={6}
              fill="#ffffff"
            />
            <text
              x={normalizedCoords[0].x}
              y={normalizedCoords[0].y - 12}
              textAnchor="middle"
              fontSize={10}
              fill="#ffffff"
            >
              START
            </text>
          </g>
        )}

        {/* Incident markers */}
        {incidents.map((incident, index) => (
          <IncidentFlag
            key={`incident-${index}`}
            incident={incident}
            track={currentTrack}
            viewBoxWidth={viewBoxWidth}
            viewBoxHeight={viewBoxHeight}
          />
        ))}

        {/* Driver dots */}
        {sortedPositions.map((position) => {
          const driver = getDriverInfo(position.driver_number);
          if (!driver) return null;

          const color = getDriverColor(driver);
          const isSelected = selectedDrivers.includes(position.driver_number);
          const isHovered = hoveredDriver === position.driver_number;

          // Normalize position to viewBox
          const normalizedPos = normalizePosition(
            position.x,
            position.y,
            viewBoxWidth,
            viewBoxHeight
          );

          return (
            <DriverDot
              key={position.driver_number}
              driver={driver}
              position={{ ...position, x: normalizedPos.x, y: normalizedPos.y }}
              color={color}
              isSelected={isSelected}
              isHovered={isHovered}
              dotSize={sizeConfig.dotSize}
              fontSize={sizeConfig.fontSize}
              onClick={() => onDriverClick?.(position.driver_number)}
              onHover={(hovered) => 
                handleDriverHover(hovered ? position.driver_number : null)
              }
            />
          );
        })}

        {/* Tooltip for hovered driver */}
        <AnimatePresence>
          {hoveredDriver && (() => {
            const position = positions.find(p => p.driver_number === hoveredDriver);
            const driver = getDriverInfo(hoveredDriver);
            if (!position || !driver) return null;

            const normalizedPos = normalizePosition(
              position.x,
              position.y,
              viewBoxWidth,
              viewBoxHeight
            );

            return (
              <DriverTooltip
                driver={driver}
                position={position}
                color={getDriverColor(driver)}
                x={normalizedPos.x}
                y={normalizedPos.y}
              />
            );
          })()}
        </AnimatePresence>
      </svg>

      {/* Track info footer */}
      <div className="absolute bottom-2 left-3 right-3 flex justify-between text-xs text-gray-500">
        <span>{currentTrack.length_km} km • {currentTrack.turns} turns</span>
        <span>{currentTrack.direction === 'clockwise' ? '↻' : '↺'}</span>
      </div>
    </div>
  );
}

// Export track utilities
export { TRACKS, getTrackByKey, getTrackByName, DEFAULT_TRACK };
export type { TrackData };
