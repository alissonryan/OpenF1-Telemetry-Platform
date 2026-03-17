/**
 * Format lap time from seconds to F1 format (M:SS.mmm)
 */
export function formatLapTime(seconds: number): string {
  if (seconds <= 0) return '--:--.---';

  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;

  return `${minutes}:${secs.toFixed(3).padStart(6, '0')}`;
}

/**
 * Format gap time
 */
export function formatGap(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '---';
  if (seconds < 0) return seconds.toFixed(3);
  return `+${seconds.toFixed(3)}`;
}

/**
 * Get team color hex code
 */
export function getTeamColor(teamName: string): string {
  const teamColors: Record<string, string> = {
    'Red Bull Racing': '#0600EF',
    'Ferrari': '#DC0000',
    'Mercedes': '#00D2BE',
    'McLaren': '#FF8700',
    'Aston Martin': '#006F62',
    'Alpine': '#0090FF',
    'Williams': '#005AFF',
    'AlphaTauri': '#2B4562',
    'Alfa Romeo': '#900000',
    'Haas F1 Team': '#FFFFFF',
    'RB': '#6692FF',
    'Kick Sauber': '#52E252',
  };
  return teamColors[teamName] || '#38383F';
}

/**
 * Format speed (km/h)
 */
export function formatSpeed(speed: number): string {
  return `${Math.round(speed)} km/h`;
}

/**
 * Format percentage
 */
export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}
