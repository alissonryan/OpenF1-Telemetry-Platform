"""
Fantasy F1 Predictor - ML model for predicting Fantasy F1 points.
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


# Fantasy F1 Scoring Rules (based on official F1 Fantasy)
QUALIFYING_POINTS = {
    1: 10, 2: 9, 3: 8, 4: 7, 5: 6,
    6: 5, 7: 4, 8: 3, 9: 2, 10: 1
}

RACE_POINTS = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

CONSTRUCTOR_POINTS_MULTIPLIER = 0.5  # Constructors get half points

BONUS_POINTS = {
    'fastest_lap': 1,  # Only if finish in top 10
    'pole_position': 1,
    'driver_of_the_day': 10,
    'overtake': 1,  # Per position gained
}


@dataclass
class FantasyPrediction:
    """Fantasy points prediction for a driver."""
    driver_id: int
    driver_name: str
    team_name: str
    price: float  # in millions
    
    # Predictions
    expected_qualifying_position: int
    expected_race_position: int
    expected_overtakes: int
    expected_fastest_lap: bool
    expected_pole: bool
    
    # Points breakdown
    qualifying_points: float
    race_points: float
    overtake_points: float
    bonus_points: float
    total_expected_points: float
    
    # Value metrics
    points_per_million: float
    confidence: float
    
    # Risk assessment
    risk_level: str  # 'low', 'medium', 'high'
    reasons: List[str]


@dataclass
class TeamRecommendation:
    """Optimal team recommendation."""
    drivers: List[FantasyPrediction]
    constructor: Dict
    total_cost: float
    total_expected_points: float
    remaining_budget: float
    budget_efficiency: float  # points per million


class FantasyPredictor:
    """ML-based Fantasy F1 points predictor."""
    
    # Driver prices (2024 season, in millions)
    DRIVER_PRICES = {
        1: 33.5,   # VER
        11: 29.8,  # PER
        16: 28.2,  # LEC
        55: 25.5,  # SAI
        44: 24.8,  # HAM
        14: 22.3,  # ALO
        63: 21.5,  # RUS
        4: 19.8,   # NOR
        81: 18.2,  # PIA
        27: 16.5,  # HUL
        22: 15.8,  # TSU
        10: 14.2,  # GAS
        31: 13.5,  # OCO
        23: 12.8,  # ALB
        77: 11.5,  # BOT
        24: 10.8,  # ZHO
        3: 9.5,    # RIC
        18: 8.2,   # STR
        20: 7.5,   # MAG
        2: 6.8,    # SAR
    }
    
    # Constructor prices (in millions)
    CONSTRUCTOR_PRICES = {
        'Red Bull Racing': 38.5,
        'Ferrari': 35.2,
        'Mercedes': 32.8,
        'McLaren': 28.5,
        'Aston Martin': 25.2,
        'Alpine': 22.8,
        'Williams': 18.5,
        'RB': 16.2,
        'Kick Sauber': 14.5,
        'Haas F1 Team': 12.8,
    }
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load or train the prediction model."""
        # For now, use rule-based predictions
        # In production, load trained XGBoost model
        logger.info("Fantasy predictor initialized with rule-based model")
    
    def predict_points(
        self,
        driver_id: int,
        driver_name: str,
        team_name: str,
        circuit_id: Optional[str] = None,
        weather: Optional[Dict] = None,
        form: Optional[Dict] = None,
    ) -> FantasyPrediction:
        """
        Predict fantasy points for a driver in the next race.
        
        Args:
            driver_id: Driver number
            driver_name: Driver name
            team_name: Team/constructor name
            circuit_id: Circuit identifier
            weather: Weather conditions
            form: Recent form data
        
        Returns:
            FantasyPrediction with expected points
        """
        price = self.DRIVER_PRICES.get(driver_id, 15.0)
        
        # Predict positions based on team strength and recent form
        team_strength = self._get_team_strength(team_name)
        circuit_factor = self._get_circuit_factor(driver_id, circuit_id) if circuit_id else 1.0
        weather_factor = self._get_weather_factor(driver_id, weather) if weather else 1.0
        form_factor = self._get_form_factor(form) if form else 1.0
        
        # Calculate expected positions
        base_qualifying_pos = self._get_base_qualifying_position(team_strength)
        base_race_pos = self._get_base_race_position(team_strength)
        
        expected_qualifying = max(1, int(base_qualifying_pos * circuit_factor * form_factor))
        expected_race = max(1, int(base_race_pos * circuit_factor * weather_factor * form_factor))
        
        # Calculate points
        qualifying_points = QUALIFYING_POINTS.get(expected_qualifying, 0)
        race_points = RACE_POINTS.get(expected_race, 0)
        
        # Overtakes (positions gained from grid to finish)
        expected_overtakes = max(0, expected_qualifying - expected_race)
        overtake_points = expected_overtakes * BONUS_POINTS['overtake']
        
        # Bonuses
        bonus_points = 0
        expected_pole = expected_qualifying == 1
        expected_fastest_lap = expected_race <= 5  # Top 5 finishers more likely to get FL
        
        if expected_pole:
            bonus_points += BONUS_POINTS['pole_position']
        if expected_fastest_lap:
            # 20% chance of fastest lap for top 5
            bonus_points += BONUS_POINTS['fastest_lap'] * 0.2
        
        total_points = qualifying_points + race_points + overtake_points + bonus_points
        
        # Value metric
        points_per_million = total_points / price if price > 0 else 0
        
        # Confidence based on team strength
        confidence = min(0.95, 0.5 + team_strength * 0.3)
        
        # Risk level
        risk_level = self._calculate_risk(expected_race, team_strength, weather_factor)
        
        # Reasons
        reasons = self._generate_reasons(
            expected_qualifying, expected_race, team_name,
            expected_overtakes, expected_fastest_lap, expected_pole
        )
        
        return FantasyPrediction(
            driver_id=driver_id,
            driver_name=driver_name,
            team_name=team_name,
            price=price,
            expected_qualifying_position=expected_qualifying,
            expected_race_position=expected_race,
            expected_overtakes=expected_overtakes,
            expected_fastest_lap=expected_fastest_lap,
            expected_pole=expected_pole,
            qualifying_points=qualifying_points,
            race_points=race_points,
            overtake_points=overtake_points,
            bonus_points=bonus_points,
            total_expected_points=round(total_points, 1),
            points_per_million=round(points_per_million, 2),
            confidence=round(confidence, 2),
            risk_level=risk_level,
            reasons=reasons,
        )
    
    def recommend_team(
        self,
        budget: float = 100.0,
        must_include: Optional[List[int]] = None,
        exclude: Optional[List[int]] = None,
    ) -> TeamRecommendation:
        """
        Recommend optimal team within budget.
        
        Uses knapsack-style optimization to maximize points.
        """
        must_include = must_include or []
        exclude = exclude or []
        
        # Get predictions for all drivers
        all_predictions = []
        for driver_id, price in self.DRIVER_PRICES.items():
            if driver_id in exclude:
                continue
            
            # Get driver/team info (simplified)
            driver_name = f"Driver {driver_id}"
            team_name = self._get_team_for_driver(driver_id)
            
            pred = self.predict_points(driver_id, driver_name, team_name)
            all_predictions.append(pred)
        
        # Sort by value (points per million)
        all_predictions.sort(key=lambda x: x.points_per_million, reverse=True)
        
        # Select 5 drivers within budget
        selected = []
        remaining_budget = budget
        
        # First, add must-include drivers
        for driver_id in must_include:
            pred = next((p for p in all_predictions if p.driver_id == driver_id), None)
            if pred and pred.price <= remaining_budget:
                selected.append(pred)
                remaining_budget -= pred.price
        
        # Then add best value drivers
        for pred in all_predictions:
            if len(selected) >= 5:
                break
            if pred.driver_id in [d.driver_id for d in selected]:
                continue
            if pred.price <= remaining_budget:
                selected.append(pred)
                remaining_budget -= pred.price
        
        # Select constructor (best value)
        constructor = self._recommend_constructor(selected, remaining_budget)
        if constructor:
            remaining_budget -= constructor['price']
        
        total_cost = sum(d.price for d in selected) + (constructor['price'] if constructor else 0)
        total_points = sum(d.total_expected_points for d in selected) + (constructor.get('expected_points', 0) if constructor else 0)
        
        return TeamRecommendation(
            drivers=selected,
            constructor=constructor or {},
            total_cost=round(total_cost, 1),
            total_expected_points=round(total_points, 1),
            remaining_budget=round(remaining_budget, 1),
            budget_efficiency=round(total_points / total_cost, 2) if total_cost > 0 else 0,
        )
    
    def get_value_plays(self, limit: int = 10) -> List[FantasyPrediction]:
        """Get best value plays (highest points per million)."""
        predictions = []
        
        for driver_id, price in self.DRIVER_PRICES.items():
            driver_name = f"Driver {driver_id}"
            team_name = self._get_team_for_driver(driver_id)
            pred = self.predict_points(driver_id, driver_name, team_name)
            predictions.append(pred)
        
        # Sort by points per million
        predictions.sort(key=lambda x: x.points_per_million, reverse=True)
        
        return predictions[:limit]
    
    def compare_drivers(
        self,
        driver1_id: int,
        driver2_id: int,
        circuit_id: Optional[str] = None,
    ) -> Dict:
        """Compare two drivers for fantasy purposes."""
        team1 = self._get_team_for_driver(driver1_id)
        team2 = self._get_team_for_driver(driver2_id)
        
        pred1 = self.predict_points(driver1_id, f"Driver {driver1_id}", team1, circuit_id)
        pred2 = self.predict_points(driver2_id, f"Driver {driver2_id}", team2, circuit_id)
        
        points_diff = pred1.total_expected_points - pred2.total_expected_points
        value_diff = pred1.points_per_million - pred2.points_per_million
        
        return {
            'driver1': pred1,
            'driver2': pred2,
            'points_difference': round(points_diff, 1),
            'value_difference': round(value_diff, 2),
            'recommendation': 'driver1' if points_diff > 0 else 'driver2',
            'confidence': abs(points_diff) / max(pred1.total_expected_points, pred2.total_expected_points, 1),
        }
    
    # Helper methods
    
    def _get_team_strength(self, team_name: str) -> float:
        """Get team strength rating (0-1)."""
        strengths = {
            'Red Bull Racing': 0.95,
            'Ferrari': 0.90,
            'Mercedes': 0.85,
            'McLaren': 0.80,
            'Aston Martin': 0.75,
            'Alpine': 0.70,
            'Williams': 0.55,
            'RB': 0.60,
            'Kick Sauber': 0.50,
            'Haas F1 Team': 0.45,
        }
        return strengths.get(team_name, 0.5)
    
    def _get_base_qualifying_position(self, team_strength: float) -> int:
        """Get base qualifying position from team strength."""
        return max(1, int(20 - (team_strength * 19)))
    
    def _get_base_race_position(self, team_strength: float) -> int:
        """Get base race position from team strength."""
        return max(1, int(20 - (team_strength * 17)))
    
    def _get_circuit_factor(self, driver_id: int, circuit_id: str) -> float:
        """Get circuit-specific performance factor."""
        # Simplified - would use historical data
        return 1.0
    
    def _get_weather_factor(self, driver_id: int, weather: Dict) -> float:
        """Get weather impact factor."""
        # Some drivers perform better in wet conditions
        wet_weather_specialists = [14, 44, 16]  # ALO, HAM, LEC
        if weather and weather.get('precipitation', 0) > 0:
            if driver_id in wet_weather_specialists:
                return 1.1
        return 1.0
    
    def _get_form_factor(self, form: Dict) -> float:
        """Get recent form factor."""
        if not form:
            return 1.0
        
        # Average of last 5 race positions vs expected
        recent_results = form.get('recent_results', [])
        if not recent_results:
            return 1.0
        
        # Better than expected = >1.0, worse = <1.0
        return 1.0 + (sum(recent_results) / len(recent_results) - 10) * 0.02
    
    def _calculate_risk(
        self,
        expected_position: int,
        team_strength: float,
        weather_factor: float,
    ) -> str:
        """Calculate risk level."""
        if team_strength > 0.8 and weather_factor >= 1.0:
            return 'low'
        elif team_strength > 0.6:
            return 'medium'
        else:
            return 'high'
    
    def _generate_reasons(
        self,
        qualifying_pos: int,
        race_pos: int,
        team_name: str,
        overtakes: int,
        fastest_lap: bool,
        pole: bool,
    ) -> List[str]:
        """Generate human-readable reasons for prediction."""
        reasons = []
        
        if pole:
            reasons.append("Strong pole position candidate")
        if qualifying_pos <= 3:
            reasons.append("Front row qualifying expected")
        if race_pos <= 3:
            reasons.append("Podium finish expected")
        if overtakes > 2:
            reasons.append(f"Expected to gain {overtakes} positions")
        if fastest_lap:
            reasons.append("Fastest lap contender")
        
        if 'Red Bull' in team_name or 'Ferrari' in team_name:
            reasons.append("Top team with consistent performance")
        elif 'Mercedes' in team_name or 'McLaren' in team_name:
            reasons.append("Strong midfield team")
        
        return reasons if reasons else ["Consistent points finisher"]
    
    def _get_team_for_driver(self, driver_id: int) -> str:
        """Get team name for driver (simplified mapping)."""
        driver_teams = {
            1: 'Red Bull Racing',
            11: 'Red Bull Racing',
            16: 'Ferrari',
            55: 'Ferrari',
            44: 'Mercedes',
            63: 'Mercedes',
            4: 'McLaren',
            81: 'McLaren',
            14: 'Aston Martin',
            18: 'Aston Martin',
            31: 'Alpine',
            10: 'Alpine',
            23: 'Williams',
            2: 'Williams',
            22: 'RB',
            3: 'RB',
            77: 'Kick Sauber',
            24: 'Kick Sauber',
            20: 'Haas F1 Team',
            27: 'Haas F1 Team',
        }
        return driver_teams.get(driver_id, 'Unknown Team')
    
    def _recommend_constructor(
        self,
        drivers: List[FantasyPrediction],
        remaining_budget: float,
    ) -> Optional[Dict]:
        """Recommend best constructor within budget."""
        # Get drivers' teams
        teams = [d.team_name for d in drivers]
        
        # Find best value constructor
        best_constructor = None
        best_value = 0
        
        for name, price in self.CONSTRUCTOR_PRICES.items():
            if price > remaining_budget:
                continue
            
            team_strength = self._get_team_strength(name)
            expected_points = team_strength * 50  # Simplified
            value = expected_points / price
            
            # Bonus if we already have their drivers
            if teams.count(name) > 0:
                value *= 1.2
            
            if value > best_value:
                best_value = value
                best_constructor = {
                    'name': name,
                    'price': price,
                    'expected_points': round(expected_points, 1),
                    'value': round(value, 2),
                }
        
        return best_constructor


# Singleton instance
_fantasy_predictor: Optional[FantasyPredictor] = None


def get_fantasy_predictor() -> FantasyPredictor:
    """Get or create fantasy predictor singleton."""
    global _fantasy_predictor
    if _fantasy_predictor is None:
        _fantasy_predictor = FantasyPredictor()
    return _fantasy_predictor
