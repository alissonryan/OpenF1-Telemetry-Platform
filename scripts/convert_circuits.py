#!/usr/bin/env python3
"""
Convert f1-circuits GeoJSON to normalized track data for the F1 Telemetry Platform.
"""
import json
import os
from pathlib import Path

def normalize_coordinates(coords, target_min=0, target_max=1000):
    """Normalize coordinates to target range."""
    if not coords:
        return []

    # Extract x and y values
    x_values = [c[0] for c in coords]
    y_values = [c[1] for c in coords]

    # Find min/max
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)

    # Normalize
    normalized = []
    for x, y in coords:
        norm_x = ((x - x_min) / (x_max - x_min) * (target_max - target_min) + target_min) if x_max != x_min else target_min
        norm_y = ((y - y_min) / (y_max - y_min) * (target_max - target_min) + target_min) if y_max != y_min else target_min
        normalized.append({"x": int(norm_x), "y": int(norm_y)})

    return normalized

def convert_geojson_to_track_data():
    """Convert GeoJSON circuits to track data format."""
    # Load data
    with open('data/circuits/circuits.geojson', 'r') as f:
        geojson = json.load(f)

    with open('data/circuits/locations.json', 'r') as f:
        locations = json.load(f)

    # Create location lookup
    location_map = {loc['id']: loc for loc in locations}

    # Circuit metadata (manual data for better accuracy)
    circuit_metadata = {
        'bh-2002': {'country_code': 'BRN', 'length_km': 5.412, 'turns': 15, 'sectors': 3, 'drs_zones': 3},
        'sa-2021': {'country_code': 'KSA', 'length_km': 6.174, 'turns': 27, 'sectors': 3, 'drs_zones': 3},
        'au-1953': {'country_code': 'AUS', 'length_km': 5.278, 'turns': 14, 'sectors': 3, 'drs_zones': 4},
        'mc-1929': {'country_code': 'MON', 'length_km': 3.337, 'turns': 19, 'sectors': 3, 'drs_zones': 1},
        'gb-1948': {'country_code': 'GBR', 'length_km': 5.891, 'turns': 18, 'sectors': 3, 'drs_zones': 2},
        'it-1922': {'country_code': 'ITA', 'length_km': 5.793, 'turns': 11, 'sectors': 3, 'drs_zones': 2},
        'be-1925': {'country_code': 'BEL', 'length_km': 7.004, 'turns': 19, 'sectors': 3, 'drs_zones': 2},
        'hu-1986': {'country_code': 'HUN', 'length_km': 4.381, 'turns': 14, 'sectors': 3, 'drs_zones': 1},
        'sg-2008': {'country_code': 'SGP', 'length_km': 4.940, 'turns': 23, 'sectors': 3, 'drs_zones': 2},
        'jp-1962': {'country_code': 'JPN', 'length_km': 5.807, 'turns': 18, 'sectors': 3, 'drs_zones': 1},
        'ae-2009': {'country_code': 'UAE', 'length_km': 5.554, 'turns': 16, 'sectors': 3, 'drs_zones': 2},
        'br-1940': {'country_code': 'BRA', 'length_km': 4.309, 'turns': 15, 'sectors': 3, 'drs_zones': 1},
        'us-2012': {'country_code': 'USA', 'length_km': 5.513, 'turns': 20, 'sectors': 3, 'drs_zones': 2},
        'mx-1962': {'country_code': 'MEX', 'length_km': 4.304, 'turns': 17, 'sectors': 3, 'drs_zones': 3},
        'at-1969': {'country_code': 'AUT', 'length_km': 4.318, 'turns': 10, 'sectors': 3, 'drs_zones': 3},
        'ca-1978': {'country_code': 'CAN', 'length_km': 4.361, 'turns': 14, 'sectors': 3, 'drs_zones': 2},
        'fr-1969': {'country_code': 'FRA', 'length_km': 5.842, 'turns': 15, 'sectors': 3, 'drs_zones': 2},
        'nl-1948': {'country_code': 'NED', 'length_km': 4.259, 'turns': 14, 'sectors': 3, 'drs_zones': 2},
        'us-2022': {'country_code': 'USA', 'length_km': 5.412, 'turns': 19, 'sectors': 3, 'drs_zones': 3},
        'az-2016': {'country_code': 'AZE', 'length_km': 6.003, 'turns': 20, 'sectors': 3, 'drs_zones': 2},
        'cn-2004': {'country_code': 'CHN', 'length_km': 5.451, 'turns': 16, 'sectors': 3, 'drs_zones': 2},
        'es-1991': {'country_code': 'ESP', 'length_km': 4.657, 'turns': 16, 'sectors': 3, 'drs_zones': 2},
        'qa-2004': {'country_code': 'QAT', 'length_km': 5.380, 'turns': 16, 'sectors': 3, 'drs_zones': 1},
        'us-2023': {'country_code': 'USA', 'length_km': 6.201, 'turns': 17, 'sectors': 3, 'drs_zones': 2},
    }

    tracks = []

    for feature in geojson['features']:
        circuit_id = feature['properties'].get('id', '')
        location_info = location_map.get(circuit_id, {})

        # Get coordinates from geometry
        coords = []
        if feature['geometry']['type'] == 'LineString':
            coords = feature['geometry']['coordinates']
        elif feature['geometry']['type'] == 'MultiLineString':
            # Flatten MultiLineString
            for line in feature['geometry']['coordinates']:
                coords.extend(line)

        # Remove duplicate last point if same as first (closed loop)
        if coords and coords[0] == coords[-1]:
            coords = coords[:-1]

        # Normalize coordinates
        normalized_coords = normalize_coordinates(coords)

        # Get metadata
        metadata = circuit_metadata.get(circuit_id, {
            'country_code': 'UNK',
            'length_km': 5.0,
            'turns': 15,
            'sectors': 3,
            'drs_zones': 2
        })

        # Calculate sectors (divide track into 3 equal parts)
        sector_boundaries = [
            {'start': 0, 'end': len(normalized_coords) // 3},
            {'start': len(normalized_coords) // 3, 'end': 2 * len(normalized_coords) // 3},
            {'start': 2 * len(normalized_coords) // 3, 'end': len(normalized_coords)}
        ]

        track = {
            'id': circuit_id,
            'name': location_info.get('name', feature['properties'].get('name', 'Unknown')),
            'location': location_info.get('location', 'Unknown'),
            'country_code': metadata['country_code'],
            'length_km': metadata['length_km'],
            'turns': metadata['turns'],
            'sectors': sector_boundaries,
            'drs_zones': metadata['drs_zones'],
            'coordinates': normalized_coords,
            'latitude': location_info.get('lat', 0),
            'longitude': location_info.get('lon', 0),
            'zoom': location_info.get('zoom', 14)
        }

        tracks.append(track)

    # Sort by name
    tracks.sort(key=lambda x: x['name'])

    return tracks

def main():
    # Convert circuits
    tracks = convert_geojson_to_track_data()

    # Save to TypeScript file
    output_dir = Path('apps/web/src/lib')
    output_dir.mkdir(parents=True, exist_ok=True)

    ts_content = """// Auto-generated track data from f1-circuits
// Source: https://github.com/bacinger/f1-circuits
// License: MIT

export interface TrackData {
  id: string;
  name: string;
  location: string;
  country_code: string;
  length_km: number;
  turns: number;
  sectors: { start: number; end: number }[];
  drs_zones: number;
  coordinates: { x: number; y: number }[];
  latitude: number;
  longitude: number;
  zoom: number;
}

export const tracks: TrackData[] = """ + json.dumps(tracks, indent=2) + """;

export function getTrackById(id: string): TrackData | undefined {
  return tracks.find(track => track.id === id);
}

export function getTrackByName(name: string): TrackData | undefined {
  return tracks.find(track => track.name.toLowerCase().includes(name.toLowerCase()));
}

export function getTrackByCountry(countryCode: string): TrackData[] {
  return tracks.filter(track => track.country_code === countryCode.toUpperCase());
}
"""

    with open(output_dir / 'allTracks.ts', 'w') as f:
        f.write(ts_content)

    print(f"✅ Converted {len(tracks)} circuits!")
    print(f"📁 Output: {output_dir / 'allTracks.ts'}")
    print(f"\n📊 Circuit list:")
    for track in tracks:
        print(f"  - {track['name']} ({track['location']}, {track['country_code']})")

if __name__ == '__main__':
    main()
