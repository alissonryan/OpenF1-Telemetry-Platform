/**
 * Track data for F1 circuits.
 *
 * Coordinates are normalized to a 0-1000 scale for consistent rendering.
 * Built from the comprehensive allTracks.ts library (f1-circuits).
 */

import { tracks as allTracksRaw, TrackData as AllTrackData } from './allTracks';

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

// ==================== Sector Colors ====================

const SECTOR_COLORS = ['#00d2be', '#ff8700', '#e10600'];

// ==================== Country Code to Country Name ====================

const COUNTRY_MAP: Record<string, string> = {
  AUS: 'Australia',
  BRN: 'Bahrain',
  KSA: 'Saudi Arabia',
  AZE: 'Azerbaijan',
  USA: 'United States',
  MON: 'Monaco',
  ESP: 'Spain',
  CAN: 'Canada',
  GBR: 'Great Britain',
  HUN: 'Hungary',
  BEL: 'Belgium',
  NED: 'Netherlands',
  ITA: 'Italy',
  SGP: 'Singapore',
  JPN: 'Japan',
  QAT: 'Qatar',
  MEX: 'Mexico',
  BRA: 'Brazil',
  UAE: 'United Arab Emirates',
  CHN: 'China',
  AUT: 'Austria',
  FRA: 'France',
};

// ==================== Location Aliases ====================
// Maps OpenF1 meeting locations / common names to allTracks location or name

const LOCATION_ALIASES: Record<string, string> = {
  // OpenF1 location -> allTracks location/name (lowercased for matching)
  'sakhir': 'sakhir',
  'bahrain': 'sakhir',
  'jeddah': 'jeddah',
  'saudi arabia': 'jeddah',
  'melbourne': 'melbourne',
  'australia': 'melbourne',
  'albert park': 'melbourne',
  'baku': 'baku',
  'azerbaijan': 'baku',
  'miami': 'miami',
  'imola': 'imola',
  'emilia romagna': 'imola',
  'monaco': 'monaco',
  'monte carlo': 'monaco',
  'monte-carlo': 'monaco',
  'barcelona': 'barcelona',
  'spain': 'barcelona',
  'catalunya': 'barcelona',
  'montreal': 'montreal',
  'canada': 'montreal',
  'silverstone': 'silverstone',
  'great britain': 'silverstone',
  'britain': 'silverstone',
  'spielberg': 'spielberg',
  'austria': 'spielberg',
  'red bull ring': 'spielberg',
  'budapest': 'budapest',
  'hungary': 'budapest',
  'hungaroring': 'budapest',
  'spa': 'spa francorchamps',
  'spa-francorchamps': 'spa francorchamps',
  'spa francorchamps': 'spa francorchamps',
  'belgium': 'spa francorchamps',
  'zandvoort': 'zandvoort',
  'netherlands': 'zandvoort',
  'dutch': 'zandvoort',
  'monza': 'monza',
  'italy': 'monza',
  'singapore': 'singapore',
  'marina bay': 'singapore',
  'suzuka': 'suzuka',
  'japan': 'suzuka',
  'lusail': 'lusail',
  'qatar': 'lusail',
  'austin': 'austin',
  'cota': 'austin',
  'united states': 'austin',
  'mexico city': 'mexico city',
  'mexico': 'mexico city',
  'sao paulo': 'sao paulo',
  'são paulo': 'sao paulo',
  'brazil': 'sao paulo',
  'interlagos': 'sao paulo',
  'las vegas': 'las vegas',
  'yas marina': 'yas marina',
  'abu dhabi': 'yas marina',
  'shanghai': 'shanghai',
  'china': 'shanghai',
  'le castellet': 'le castellet',
  'paul ricard': 'le castellet',
  'france': 'le castellet',
  'hockenheim': 'hockenheim',
  'hockenheimring': 'hockenheim',
  'germany': 'hockenheim',
  'nürburgring': 'nürburg',
  'nurburgring': 'nürburg',
  'portimão': 'portimão',
  'portimao': 'portimão',
  'portugal': 'portimão',
  'algarve': 'portimão',
  'istanbul': 'istanbul',
  'turkey': 'istanbul',
  'sochi': 'sochi',
  'russia': 'sochi',
  'sepang': 'sepang',
  'malaysia': 'sepang',
  'mugello': 'scarperia e san piero',
  'johannesburg': 'johannesburg',
  'south africa': 'johannesburg',
  'kyalami': 'johannesburg',
  'madrid': 'madrid',
  'indianapolis': 'indianapolis',
};

// ==================== Coordinate Normalization ====================

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

// ==================== Conversion ====================

/**
 * Convert an allTracks entry to the TrackData format used by TrackMap
 */
function convertTrack(source: AllTrackData, index: number): TrackData {
  const country = COUNTRY_MAP[source.country_code] || source.country_code;

  // Convert sectors and add default colors
  const sectors: TrackSector[] = source.sectors.map((sector, i) => ({
    start: sector.start,
    end: sector.end,
    color: SECTOR_COLORS[i % SECTOR_COLORS.length],
  }));

  return {
    circuit_key: index + 1,
    name: source.name,
    official_name: source.name,
    country,
    location: source.location,
    length_km: source.length_km,
    turns: source.turns,
    sectors,
    coordinates: normalizeCoords(source.coordinates),
    drs_zones: [],
    direction: 'clockwise',
  };
}

// ==================== Build TRACKS ====================

/**
 * Track data for all supported circuits, built from allTracks.ts
 */
export const TRACKS: TrackData[] = allTracksRaw.map((t, i) => convertTrack(t, i));

// ==================== Lookup Functions ====================

/**
 * Get track data by circuit key
 */
export function getTrackByKey(circuitKey: number): TrackData | undefined {
  return TRACKS.find(track => track.circuit_key === circuitKey);
}

/**
 * Resolve a location alias to the canonical allTracks location (lowercased)
 */
function resolveAlias(input: string): string | undefined {
  return LOCATION_ALIASES[input.toLowerCase()];
}

/**
 * Get track data by circuit name with fuzzy matching.
 *
 * Matching strategy (in order of priority):
 * 1. Exact match on location or name (case-insensitive)
 * 2. Known alias mapping (e.g. "Sakhir" -> Bahrain, "Melbourne" -> Albert Park)
 * 3. Substring match on name or location
 * 4. Word-boundary match (any word in the query appears in name/location)
 */
export function getTrackByName(name: string): TrackData | undefined {
  if (!name) return undefined;

  const query = name.toLowerCase().trim();

  // 1. Exact match on location or name
  const exact = TRACKS.find(
    t =>
      t.location.toLowerCase() === query ||
      t.name.toLowerCase() === query ||
      t.official_name.toLowerCase() === query
  );
  if (exact) return exact;

  // 2. Alias mapping
  const aliasTarget = resolveAlias(query);
  if (aliasTarget) {
    const aliased = TRACKS.find(
      t =>
        t.location.toLowerCase() === aliasTarget ||
        t.name.toLowerCase().includes(aliasTarget)
    );
    if (aliased) return aliased;
  }

  // 3. Substring match — query appears within name or location
  const substring = TRACKS.find(
    t =>
      t.name.toLowerCase().includes(query) ||
      t.location.toLowerCase().includes(query) ||
      t.official_name.toLowerCase().includes(query)
  );
  if (substring) return substring;

  // 4. Word-boundary match — any query word (3+ chars) appears in name/location
  const words = query.split(/\s+/).filter(w => w.length >= 3);
  if (words.length > 0) {
    const wordMatch = TRACKS.find(t => {
      const haystack = `${t.name} ${t.location} ${t.official_name}`.toLowerCase();
      return words.some(w => haystack.includes(w));
    });
    if (wordMatch) return wordMatch;
  }

  return undefined;
}

// ==================== Track Utility Functions ====================

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
 * Default track (first track — Albert Park Circuit)
 */
export const DEFAULT_TRACK = TRACKS[0];
