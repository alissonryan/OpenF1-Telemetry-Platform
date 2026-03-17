"""
Strategy recommendation model for optimal pit stop strategies.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

import numpy as np
import pandas as pd
from dataclasses import dataclass
import joblib

from app.core.config import settings
from app.core.logging import logger


class RiskLevel(str, Enum):
    """Risk level for strategy recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Compound(str, Enum):
    """Tyre compound types."""
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


@dataclass
class PitStopRecommendation:
    """Single pit stop recommendation."""
    lap: int
    compound: str
    reason: str


@dataclass
class StrategyResult:
    """Complete strategy recommendation result."""
    recommended_stops: int
    optimal_laps: List[int]
    compounds: List[str]
    risk_level: str
    expected_positions_gained: float
    confidence: float
    alternative_strategies: List[Dict]
    factors: List[str]


class StrategyRecommender:
    """ML-based strategy recommender for F1 races."""

    def __init__(self):
        self.is_trained = False
        self.model = None
        
        # Compound performance characteristics (relative lap time delta)
        self.compound_characteristics = {
            "SOFT": {"pace_advantage": 0.8, "degradation_rate": 0.15, "optimal_stint": 15},
            "MEDIUM": {"pace_advantage": 0.0, "degradation_rate": 0.08, "optimal_stint": 25},
            "HARD": {"pace_advantage": -0.6, "degradation_rate": 0.05, "optimal_stint": 35},
            "INTERMEDIATE": {"pace_advantage": 0.0, "degradation_rate": 0.1, "optimal_stint": 20},
            "WET": {"pace_advantage": 0.0, "degradation_rate": 0.07, "optimal_stint": 25},
        }
        
        # Typical race lap counts by circuit type
        self.circuit_laps = {
            "Monaco": 78,
            "Spa": 44,
            "Monza": 53,
            "Silverstone": 52,
            "Bahrain": 57,
            "default": 50,
        }

    def recommend_strategy(
        self,
        session_data: Dict,
        driver_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generate pit stop strategy recommendations.

        Args:
            session_data: Dictionary containing session information
            driver_data: Optional specific driver data for personalized recommendation

        Returns:
            Dictionary with strategy recommendations
        """
        current_lap = session_data.get("current_lap", 0)
        total_laps = session_data.get("total_laps", 50)
        current_compound = session_data.get("current_compound", "MEDIUM")
        tyre_age = session_data.get("tyre_age", 0)
        position = session_data.get("position", 10)
        track_temp = session_data.get("track_temp", 30)
        weather = session_data.get("weather", "dry")
        
        remaining_laps = total_laps - current_lap
        
        # Determine optimal strategy based on race situation
        strategy = self._calculate_optimal_strategy(
            remaining_laps=remaining_laps,
            current_lap=current_lap,
            current_compound=current_compound,
            tyre_age=tyre_age,
            position=position,
            track_temp=track_temp,
            weather=weather,
        )
        
        return {
            "driver_number": session_data.get("driver_number"),
            "recommended_stops": strategy.recommended_stops,
            "optimal_laps": strategy.optimal_laps,
            "compounds": strategy.compounds,
            "risk_level": strategy.risk_level,
            "expected_positions_gained": round(strategy.expected_positions_gained, 1),
            "confidence": round(strategy.confidence, 3),
            "alternative_strategies": strategy.alternative_strategies,
            "factors": strategy.factors,
        }

    def _calculate_optimal_strategy(
        self,
        remaining_laps: int,
        current_lap: int,
        current_compound: str,
        tyre_age: int,
        position: int,
        track_temp: float,
        weather: str,
    ) -> StrategyResult:
        """Calculate optimal pit stop strategy."""
        
        factors = []
        
        # Adjust for weather
        if weather == "wet":
            factors.append("Wet conditions - flexibility key")
            return self._wet_weather_strategy(remaining_laps, current_lap)
        
        # Check if current tyres can go to end
        compound_chars = self.compound_characteristics.get(current_compound, {})
        optimal_stint = compound_chars.get("optimal_stint", 25)
        
        if tyre_age + remaining_laps <= optimal_stint * 1.2:
            # Can potentially one-stop or no-stop
            if position <= 5:
                factors.append("Track position critical - consider extending stint")
                return self._conservative_strategy(remaining_laps, current_lap, current_compound)
        
        # Determine number of stops needed
        if remaining_laps <= 20:
            recommended_stops = 0 if tyre_age < 15 else 1
        elif remaining_laps <= 35:
            recommended_stops = 1
        else:
            recommended_stops = 2
        
        # Calculate optimal pit windows
        optimal_laps = self._calculate_pit_windows(
            current_lap, remaining_laps, recommended_stops, current_compound
        )
        
        # Determine compounds
        compounds = self._select_compounds(
            current_compound, recommended_stops, remaining_laps, track_temp
        )
        
        # Calculate risk level
        risk_level = self._assess_risk(
            recommended_stops, position, remaining_laps, tyre_age
        )
        
        # Calculate expected positions gained
        expected_gain = self._calculate_expected_gain(
            recommended_stops, position, compounds, remaining_laps
        )
        
        # Generate alternative strategies
        alternatives = self._generate_alternatives(
            recommended_stops, current_lap, remaining_laps, current_compound
        )
        
        # Add factors
        if tyre_age > optimal_stint:
            factors.append(f"Tyre age ({tyre_age}) exceeds optimal stint length")
        if position <= 5:
            factors.append("Front-running position - track position valuable")
        if remaining_laps < 15:
            factors.append("Late race - time vs position trade-off")
        if track_temp > 35:
            factors.append("High track temp - increased degradation")
        
        if not factors:
            factors.append("Standard strategy window")
        
        confidence = self._calculate_confidence(
            remaining_laps, recommended_stops, tyre_age, position
        )
        
        return StrategyResult(
            recommended_stops=recommended_stops,
            optimal_laps=optimal_laps,
            compounds=compounds,
            risk_level=risk_level,
            expected_positions_gained=expected_gain,
            confidence=confidence,
            alternative_strategies=alternatives,
            factors=factors,
        )

    def _calculate_pit_windows(
        self,
        current_lap: int,
        remaining_laps: int,
        num_stops: int,
        current_compound: str,
    ) -> List[int]:
        """Calculate optimal lap windows for pit stops."""
        if num_stops == 0:
            return []
        
        if num_stops == 1:
            # Single stop: aim for middle of remaining race
            optimal_lap = current_lap + int(remaining_laps * 0.5)
            return [max(current_lap + 3, optimal_lap)]
        
        # Two stops: divide race into thirds
        stop1 = current_lap + int(remaining_laps * 0.33)
        stop2 = current_lap + int(remaining_laps * 0.66)
        
        return [stop1, stop2]

    def _select_compounds(
        self,
        current_compound: str,
        num_stops: int,
        remaining_laps: int,
        track_temp: float,
    ) -> List[str]:
        """Select optimal compounds for each stint."""
        if num_stops == 0:
            return []
        
        compounds = []
        
        # For first stop
        if remaining_laps > 25:
            # Longer remaining: prefer harder compound
            if current_compound == "SOFT":
                compounds.append("HARD")
            else:
                compounds.append("MEDIUM")
        else:
            # Shorter remaining: can use softer
            compounds.append("MEDIUM")
        
        # For second stop
        if num_stops > 1:
            final_stint = remaining_laps // 3
            if final_stint < 15:
                compounds.append("SOFT")
            else:
                compounds.append("MEDIUM")
        
        return compounds

    def _assess_risk(
        self,
        num_stops: int,
        position: int,
        remaining_laps: int,
        tyre_age: int,
    ) -> str:
        """Assess risk level of the strategy."""
        risk_score = 0
        
        # More stops = higher risk (traffic, safety car timing)
        risk_score += num_stops * 2
        
        # Front positions = higher risk (more to lose)
        if position <= 3:
            risk_score += 3
        elif position <= 10:
            risk_score += 1
        
        # Old tyres = higher risk if not pitting
        if num_stops == 0 and tyre_age > 20:
            risk_score += 3
        
        # Few remaining laps = higher risk for stops
        if remaining_laps < 15 and num_stops > 0:
            risk_score += 2
        
        if risk_score <= 3:
            return RiskLevel.LOW.value
        elif risk_score <= 6:
            return RiskLevel.MEDIUM.value
        else:
            return RiskLevel.HIGH.value

    def _calculate_expected_gain(
        self,
        num_stops: int,
        position: int,
        compounds: List[str],
        remaining_laps: int,
    ) -> float:
        """Calculate expected positions gained/lost."""
        # Base expectation
        expected_gain = 0
        
        # Pace advantage from fresh tyres
        for compound in compounds:
            chars = self.compound_characteristics.get(compound, {})
            expected_gain += chars.get("pace_advantage", 0) * 0.5
        
        # Track position loss from stops
        expected_gain -= num_stops * 2.5
        
        # Adjust for starting position
        if position <= 5:
            expected_gain -= 0.5  # Harder to gain from front
        
        return expected_gain

    def _calculate_confidence(
        self,
        remaining_laps: int,
        num_stops: int,
        tyre_age: int,
        position: int,
    ) -> float:
        """Calculate confidence in the recommendation."""
        confidence = 0.5
        
        # More remaining laps = more uncertainty
        if remaining_laps < 20:
            confidence += 0.2
        elif remaining_laps < 35:
            confidence += 0.1
        
        # Standard strategies = higher confidence
        if num_stops in [1, 2]:
            confidence += 0.15
        
        return min(0.9, max(0.4, confidence))

    def _wet_weather_strategy(
        self,
        remaining_laps: int,
        current_lap: int,
    ) -> StrategyResult:
        """Generate wet weather strategy."""
        return StrategyResult(
            recommended_stops=1,  # Flexible stop
            optimal_laps=[current_lap + max(5, remaining_laps // 3)],
            compounds=["INTERMEDIATE"],
            risk_level=RiskLevel.HIGH.value,
            expected_positions_gained=1.0,
            confidence=0.4,
            alternative_strategies=[
                {
                    "strategy": "Stay on current compound",
                    "risk": "medium",
                    "condition": "If no more rain expected",
                }
            ],
            factors=["Wet conditions require flexible strategy"],
        )

    def _conservative_strategy(
        self,
        remaining_laps: int,
        current_lap: int,
        current_compound: str,
    ) -> StrategyResult:
        """Generate conservative strategy for front-runners."""
        return StrategyResult(
            recommended_stops=1,
            optimal_laps=[current_lap + int(remaining_laps * 0.6)],
            compounds=["MEDIUM"] if current_compound != "MEDIUM" else ["HARD"],
            risk_level=RiskLevel.LOW.value,
            expected_positions_gained=-0.5,
            confidence=0.7,
            alternative_strategies=[
                {
                    "strategy": "Extended stint",
                    "risk": "medium",
                    "condition": "If tyres holding",
                }
            ],
            factors=["Conservative approach to protect track position"],
        )

    def _generate_alternatives(
        self,
        recommended_stops: int,
        current_lap: int,
        remaining_laps: int,
        current_compound: str,
    ) -> List[Dict]:
        """Generate alternative strategy options."""
        alternatives = []
        
        if recommended_stops == 1:
            # Alternative: 0-stop (if possible)
            if remaining_laps < 30:
                alternatives.append({
                    "strategy": "0-stop (extend stint)",
                    "risk": "high",
                    "expected_gain": -1.5,
                    "condition": "If tyre degradation low",
                })
            
            # Alternative: 2-stop (aggressive)
            alternatives.append({
                "strategy": "2-stop (aggressive)",
                "risk": "medium",
                "expected_gain": 1.0,
                "condition": "If pace advantage significant",
            })
        
        elif recommended_stops == 2:
            # Alternative: 1-stop (conservative)
            alternatives.append({
                "strategy": "1-stop (conservative)",
                "risk": "low",
                "expected_gain": -0.5,
                "condition": "If managing position",
            })
        
        return alternatives[:2]

    def train(self, historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the strategy model on historical data.
        
        Args:
            historical_data: DataFrame with historical race data
            
        Returns:
            Training metrics
        """
        # For now, strategy is rule-based
        # Could be enhanced with ML in future
        self.is_trained = True
        logger.info("StrategyRecommender initialized with rule-based system")
        return {"status": "initialized", "method": "rule_based"}

    def save(self, path: Optional[Path] = None) -> None:
        """Save model configuration."""
        path = path or Path(settings.models_dir) / "strategy_recommender"
        path.mkdir(parents=True, exist_ok=True)
        
        joblib.dump({
            "is_trained": self.is_trained,
            "compound_characteristics": self.compound_characteristics,
        }, path / "config.pkl")
        
        logger.info(f"StrategyRecommender saved to {path}")

    def load(self, path: Optional[Path] = None) -> None:
        """Load model configuration."""
        path = path or Path(settings.models_dir) / "strategy_recommender"
        
        try:
            config = joblib.load(path / "config.pkl")
            self.is_trained = config.get("is_trained", False)
            if "compound_characteristics" in config:
                self.compound_characteristics = config["compound_characteristics"]
            logger.info(f"StrategyRecommender loaded from {path}")
        except FileNotFoundError:
            logger.warning("No saved config, using defaults")
            self.is_trained = True
