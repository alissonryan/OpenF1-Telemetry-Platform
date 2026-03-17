/**
 * Weather types for the F1 Telemetry Platform
 * Based on Open-Meteo API weather codes
 */

export interface CurrentWeather {
  temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
  wind_gusts?: number;
  precipitation: number;
  weather_code: number;
  weather_description: string;
  is_day: boolean;
  time: string;
}

export interface HourlyForecast {
  date: string;
  hour: number;
  temp: number;
  temp_max: number;
  temp_min: number;
  precipitation_probability: number;
  precipitation_amount: number;
  weather_code: number;
  weather_description: string;
  wind_speed: number;
  wind_direction: number;
  humidity: number;
}

export interface DailyForecast {
  date: string;
  temp_max: number;
  temp_min: number;
  precipitation_probability: number;
  precipitation_sum: number;
  weather_code: number;
  weather_description: string;
  wind_speed_max: number;
  wind_gusts_max?: number;
  wind_direction: number;
  sunrise?: string;
  sunset?: string;
}

export interface WeatherData {
  circuit?: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  current: CurrentWeather;
  forecast: {
    hourly: HourlyForecast[];
    daily: DailyForecast[];
  };
}

export interface CircuitWeatherResponse {
  circuit: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  current: Record<string, unknown>;
  forecast: Record<string, unknown>;
}

export type TrackCondition = 'dry' | 'wet' | 'intermediate' | 'risk_of_rain';

export interface WeatherConditions {
  trackCondition: TrackCondition;
  visibilityGood: boolean;
  windImpact: 'low' | 'medium' | 'high';
  rainProbability: number;
}

// WMO Weather Code mappings (0-99)
export const WEATHER_CODES: Record<number, { description: string; icon: string }> = {
  // Clear
  0: { description: 'Clear sky', icon: 'clear' },
  
  // Mainly clear / partly cloudy
  1: { description: 'Mainly clear', icon: 'partly-cloudy' },
  2: { description: 'Partly cloudy', icon: 'partly-cloudy' },
  3: { description: 'Overcast', icon: 'cloudy' },
  
  // Fog
  45: { description: 'Foggy', icon: 'fog' },
  48: { description: 'Depositing rime fog', icon: 'fog' },
  
  // Drizzle
  51: { description: 'Light drizzle', icon: 'drizzle' },
  53: { description: 'Moderate drizzle', icon: 'drizzle' },
  55: { description: 'Dense drizzle', icon: 'drizzle' },
  56: { description: 'Light freezing drizzle', icon: 'drizzle' },
  57: { description: 'Dense freezing drizzle', icon: 'drizzle' },
  
  // Rain
  61: { description: 'Slight rain', icon: 'rain' },
  63: { description: 'Moderate rain', icon: 'rain' },
  65: { description: 'Heavy rain', icon: 'heavy-rain' },
  66: { description: 'Light freezing rain', icon: 'rain' },
  67: { description: 'Heavy freezing rain', icon: 'rain' },
  
  // Snow
  71: { description: 'Slight snow', icon: 'snow' },
  73: { description: 'Moderate snow', icon: 'snow' },
  75: { description: 'Heavy snow', icon: 'heavy-snow' },
  77: { description: 'Snow grains', icon: 'snow' },
  
  // Rain showers
  80: { description: 'Slight rain showers', icon: 'rain' },
  81: { description: 'Moderate rain showers', icon: 'rain' },
  82: { description: 'Violent rain showers', icon: 'heavy-rain' },
  
  // Snow showers
  85: { description: 'Slight snow showers', icon: 'snow' },
  86: { description: 'Heavy snow showers', icon: 'heavy-snow' },
  
  // Thunderstorm
  95: { description: 'Thunderstorm', icon: 'thunderstorm' },
  96: { description: 'Thunderstorm with slight hail', icon: 'thunderstorm' },
  99: { description: 'Thunderstorm with heavy hail', icon: 'thunderstorm' },
};

// Wind direction compass points
export const WIND_DIRECTIONS: Record<number, string> = {
  0: 'N',
  22.5: 'NNE',
  45: 'NE',
  67.5: 'ENE',
  90: 'E',
  112.5: 'ESE',
  135: 'SE',
  157.5: 'SSE',
  180: 'S',
  202.5: 'SSW',
  225: 'SW',
  247.5: 'WSW',
  270: 'W',
  292.5: 'WNW',
  315: 'NW',
  337.5: 'NNW',
};

export function getWeatherDescription(code: number): string {
  return WEATHER_CODES[code]?.description ?? 'Unknown';
}

export function getWeatherIcon(code: number): string {
  return WEATHER_CODES[code]?.icon ?? 'unknown';
}

export function getWindDirection(degrees: number): string {
  const normalizedDegrees = ((degrees % 360) + 360) % 360;
  const directions = Object.keys(WIND_DIRECTIONS).map(Number);
  let closest = 0;
  let minDiff = 360;
  
  for (const dir of directions) {
    const diff = Math.abs(normalizedDegrees - dir);
    if (diff < minDiff) {
      minDiff = diff;
      closest = dir;
    }
  }
  
  return WIND_DIRECTIONS[closest] ?? 'N';
}

export function getTrackCondition(
  weatherCode: number,
  precipitation: number,
  precipitationProbability: number
): TrackCondition {
  // Thunderstorm or heavy rain codes
  if ([65, 82, 95, 96, 99].includes(weatherCode)) {
    return 'wet';
  }
  
  // Rain or drizzle codes
  if ([51, 53, 55, 56, 57, 61, 63, 66, 67, 80, 81].includes(weatherCode)) {
    return precipitation > 2 ? 'wet' : 'intermediate';
  }
  
  // Snow codes
  if ([71, 73, 75, 77, 85, 86].includes(weatherCode)) {
    return 'wet';
  }
  
  // High probability of rain
  if (precipitationProbability > 70) {
    return 'risk_of_rain';
  }
  
  // Some precipitation expected
  if (precipitationProbability > 30 || precipitation > 0) {
    return 'risk_of_rain';
  }
  
  return 'dry';
}
