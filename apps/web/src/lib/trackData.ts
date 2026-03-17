/**
 * Track data for F1 circuits.
 * 
 * Coordinates are normalized to a 0-1000 scale for consistent rendering.
 * Real coordinates from OpenF1 API are in 1/10 meter units.
 */

export interface TrackSector {
  start: number; // Index of the starting point
  end: number;   // Index of the ending point
  color?: string;
}

export interface DRSZone {
  start: number; // Distance percentage along the track (0-100)
  end: number;
  detectionPoint: number; // Detection point percentage
}

export interface TrackData {
  circuit_key: number;
  name: string;
  official_name: string;
  country: string;
  location: string;
  length_km: number;
  turns: number;
  sectors: TrackSector[];
  coordinates: { x: number; y: number }[];
  drs_zones?: DRSZone[];
  direction: 'clockwise' | 'counterclockwise';
}

/**
 * Normalize coordinates to 0-1000 scale
 */
function normalizeCoords(coords: { x: number; y: number }[]): { x: number; y: number }[] {
  const xs = coords.map(c => c.x);
  const ys = coords.map(c => c.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;
  
  return coords.map(c => ({
    x: Math.round(((c.x - minX) / rangeX) * 900 + 50),
    y: Math.round(((c.y - minY) / rangeY) * 900 + 50),
  }));
}

// Bahrain International Circuit (Sakhir)
const bahrain_coords = normalizeCoords([
  { x: 100, y: 200 },
  { x: 150, y: 150 },
  { x: 250, y: 120 },
  { x: 350, y: 100 },
  { x: 450, y: 120 },
  { x: 550, y: 150 },
  { x: 650, y: 180 },
  { x: 700, y: 220 },
  { x: 730, y: 280 },
  { x: 700, y: 350 },
  { x: 650, y: 400 },
  { x: 580, y: 450 },
  { x: 500, y: 500 },
  { x: 420, y: 530 },
  { x: 350, y: 550 },
  { x: 280, y: 520 },
  { x: 220, y: 480 },
  { x: 180, y: 420 },
  { x: 150, y: 350 },
  { x: 120, y: 280 },
  { x: 100, y: 200 },
]);

// Jeddah Corniche Circuit (Saudi Arabia)
const jeddah_coords = normalizeCoords([
  { x: 100, y: 300 },
  { x: 150, y: 250 },
  { x: 200, y: 200 },
  { x: 280, y: 150 },
  { x: 380, y: 120 },
  { x: 500, y: 100 },
  { x: 600, y: 130 },
  { x: 680, y: 180 },
  { x: 720, y: 250 },
  { x: 700, y: 320 },
  { x: 650, y: 380 },
  { x: 580, y: 420 },
  { x: 500, y: 440 },
  { x: 420, y: 420 },
  { x: 380, y: 380 },
  { x: 350, y: 320 },
  { x: 300, y: 280 },
  { x: 250, y: 300 },
  { x: 200, y: 340 },
  { x: 150, y: 350 },
  { x: 100, y: 300 },
]);

// Albert Park Circuit (Australia - Melbourne)
const melbourne_coords = normalizeCoords([
  { x: 200, y: 150 },
  { x: 300, y: 120 },
  { x: 400, y: 100 },
  { x: 520, y: 130 },
  { x: 620, y: 180 },
  { x: 700, y: 250 },
  { x: 720, y: 340 },
  { x: 680, y: 420 },
  { x: 600, y: 480 },
  { x: 500, y: 520 },
  { x: 400, y: 540 },
  { x: 300, y: 520 },
  { x: 220, y: 470 },
  { x: 160, y: 400 },
  { x: 140, y: 320 },
  { x: 160, y: 240 },
  { x: 200, y: 150 },
]);

// Circuit de Monaco
const monaco_coords = normalizeCoords([
  { x: 250, y: 100 },
  { x: 350, y: 80 },
  { x: 450, y: 100 },
  { x: 520, y: 150 },
  { x: 560, y: 220 },
  { x: 540, y: 300 },
  { x: 480, y: 360 },
  { x: 400, y: 400 },
  { x: 350, y: 450 },
  { x: 320, y: 520 },
  { x: 280, y: 580 },
  { x: 220, y: 600 },
  { x: 160, y: 560 },
  { x: 140, y: 480 },
  { x: 160, y: 400 },
  { x: 200, y: 320 },
  { x: 180, y: 250 },
  { x: 200, y: 180 },
  { x: 250, y: 100 },
]);

// Silverstone Circuit (Great Britain)
const silverstone_coords = normalizeCoords([
  { x: 300, y: 600 },
  { x: 250, y: 520 },
  { x: 200, y: 440 },
  { x: 180, y: 350 },
  { x: 200, y: 260 },
  { x: 260, y: 180 },
  { x: 350, y: 120 },
  { x: 450, y: 100 },
  { x: 550, y: 130 },
  { x: 640, y: 180 },
  { x: 700, y: 260 },
  { x: 720, y: 350 },
  { x: 680, y: 440 },
  { x: 600, y: 500 },
  { x: 500, y: 530 },
  { x: 400, y: 560 },
  { x: 300, y: 600 },
]);

/**
 * Track data for all supported circuits
 */
export const TRACKS: TrackData[] = [
  {
    circuit_key: 1,
    name: 'Sakhir',
    official_name: 'Bahrain International Circuit',
    country: 'Bahrain',
    location: 'Sakhir',
    length_km: 5.412,
    turns: 15,
    sectors: [
      { start: 0, end: 6, color: '#00d2be' },
      { start: 6, end: 13, color: '#ff8700' },
      { start: 13, end: 20, color: '#e10600' },
    ],
    coordinates: bahrain_coords,
    drs_zones: [
      { start: 10, end: 18, detectionPoint: 8 },
      { start: 42, end: 52, detectionPoint: 38 },
      { start: 70, end: 82, detectionPoint: 65 },
    ],
    direction: 'clockwise',
  },
  {
    circuit_key: 2,
    name: 'Jeddah',
    official_name: 'Jeddah Corniche Circuit',
    country: 'Saudi Arabia',
    location: 'Jeddah',
    length_km: 6.174,
    turns: 27,
    sectors: [
      { start: 0, end: 7, color: '#00d2be' },
      { start: 7, end: 14, color: '#ff8700' },
      { start: 14, end: 20, color: '#e10600' },
    ],
    coordinates: jeddah_coords,
    drs_zones: [
      { start: 18, end: 28, detectionPoint: 12 },
      { start: 75, end: 88, detectionPoint: 70 },
    ],
    direction: 'clockwise',
  },
  {
    circuit_key: 3,
    name: 'Melbourne',
    official_name: 'Albert Park Circuit',
    country: 'Australia',
    location: 'Melbourne',
    length_km: 5.278,
    turns: 14,
    sectors: [
      { start: 0, end: 5, color: '#00d2be' },
      { start: 5, end: 11, color: '#ff8700' },
      { start: 11, end: 16, color: '#e10600' },
    ],
    coordinates: melbourne_coords,
    drs_zones: [
      { start: 12, end: 22, detectionPoint: 8 },
      { start: 65, end: 78, detectionPoint: 60 },
    ],
    direction: 'clockwise',
  },
  {
    circuit_key: 4,
    name: 'Monaco',
    official_name: 'Circuit de Monaco',
    country: 'Monaco',
    location: 'Monte Carlo',
    length_km: 3.337,
    turns: 19,
    sectors: [
      { start: 0, end: 6, color: '#00d2be' },
      { start: 6, end: 12, color: '#ff8700' },
      { start: 12, end: 18, color: '#e10600' },
    ],
    coordinates: monaco_coords,
    drs_zones: [], // No DRS zones at Monaco
    direction: 'clockwise',
  },
  {
    circuit_key: 5,
    name: 'Silverstone',
    official_name: 'Silverstone Circuit',
    country: 'Great Britain',
    location: 'Silverstone',
    length_km: 5.891,
    turns: 18,
    sectors: [
      { start: 0, end: 5, color: '#00d2be' },
      { start: 5, end: 11, color: '#ff8700' },
      { start: 11, end: 16, color: '#e10600' },
    ],
    coordinates: silverstone_coords,
    drs_zones: [
      { start: 5, end: 15, detectionPoint: 2 },
      { start: 50, end: 62, detectionPoint: 45 },
      { start: 82, end: 92, detectionPoint: 78 },
    ],
    direction: 'clockwise',
  },
];

/**
 * Get track data by circuit key
 */
export function getTrackByKey(circuitKey: number): TrackData | undefined {
  return TRACKS.find(track => track.circuit_key === circuitKey);
}

/**
 * Get track data by circuit name
 */
export function getTrackByName(name: string): TrackData | undefined {
  const normalizedName = name.toLowerCase();
  return TRACKS.find(
    track => 
      track.name.toLowerCase() === normalizedName ||
      track.official_name.toLowerCase().includes(normalizedName) ||
      track.location.toLowerCase() === normalizedName
  );
}

/**
 * Calculate the distance percentage along the track for a given position
 */
export function calculateTrackProgress(
  track: TrackData,
  x: number,
  y: number
): number {
  const coords = track.coordinates;
  let minDistance = Infinity;
  let closestIndex = 0;

  // Find closest point on track
  for (let i = 0; i < coords.length; i++) {
    const dx = coords[i].x - x;
    const dy = coords[i].y - y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance < minDistance) {
      minDistance = distance;
      closestIndex = i;
    }
  }

  return (closestIndex / (coords.length - 1)) * 100;
}

/**
 * Get track coordinates for a given progress percentage
 */
export function getPositionOnTrack(
  track: TrackData,
  progressPercent: number
): { x: number; y: number } {
  const coords = track.coordinates;
  const totalPoints = coords.length - 1;
  const exactIndex = (progressPercent / 100) * totalPoints;
  const index = Math.floor(exactIndex);
  const fraction = exactIndex - index;

  if (index >= totalPoints) {
    return coords[totalPoints];
  }

  const p1 = coords[index];
  const p2 = coords[index + 1];

  return {
    x: p1.x + (p2.x - p1.x) * fraction,
    y: p1.y + (p2.y - p1.y) * fraction,
  };
}

/**
 * Get sector number for a given progress percentage
 */
export function getSectorForProgress(
  track: TrackData,
  progressPercent: number
): number {
  const coords = track.coordinates;
  const totalPoints = coords.length - 1;
  const pointIndex = Math.floor((progressPercent / 100) * totalPoints);

  for (let i = 0; i < track.sectors.length; i++) {
    const sector = track.sectors[i];
    if (pointIndex >= sector.start && pointIndex <= sector.end) {
      return i + 1;
    }
  }

  return 1;
}

/**
 * Check if position is in a DRS zone
 */
export function isInDRSZone(
  track: TrackData,
  progressPercent: number
): boolean {
  if (!track.drs_zones) return false;

  return track.drs_zones.some(
    zone => progressPercent >= zone.start && progressPercent <= zone.end
  );
}

/**
 * Default track (Bahrain)
 */
export const DEFAULT_TRACK = TRACKS[0];
