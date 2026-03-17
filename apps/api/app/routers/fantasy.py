"""
Fantasy F1 API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.ml.fantasy_predictor import (
    FantasyPrediction,
    TeamRecommendation,
    get_fantasy_predictor,
)


router = APIRouter(prefix="/fantasy", tags=["Fantasy F1"])


@router.post("/predict/{driver_id}", response_model=FantasyPrediction)
async def predict_driver_points(
    driver_id: int,
    circuit_id: Optional[str] = Query(None, description="Circuit identifier"),
):
    """
    Predict fantasy points for a specific driver.
    
    Returns expected points breakdown and value metrics.
    """
    predictor = get_fantasy_predictor()
    
    try:
        # Get driver info from F1DB (simplified for now)
        driver_name = f"Driver {driver_id}"
        team_name = predictor._get_team_for_driver(driver_id)
        
        prediction = predictor.predict_points(
            driver_id=driver_id,
            driver_name=driver_name,
            team_name=team_name,
            circuit_id=circuit_id,
        )
        
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/all", response_model=List[FantasyPrediction])
async def predict_all_drivers(
    circuit_id: Optional[str] = Query(None, description="Circuit identifier"),
):
    """
    Predict fantasy points for all drivers.
    
    Returns sorted list by expected points.
    """
    predictor = get_fantasy_predictor()
    
    predictions = []
    for driver_id in predictor.DRIVER_PRICES.keys():
        try:
            driver_name = f"Driver {driver_id}"
            team_name = predictor._get_team_for_driver(driver_id)
            
            pred = predictor.predict_points(
                driver_id=driver_id,
                driver_name=driver_name,
                team_name=team_name,
                circuit_id=circuit_id,
            )
            predictions.append(pred)
        except Exception:
            continue
    
    # Sort by expected points (descending)
    predictions.sort(key=lambda x: x.total_expected_points, reverse=True)
    
    return predictions


@router.get("/recommend", response_model=TeamRecommendation)
async def recommend_team(
    budget: float = Query(100.0, ge=80, le=150, description="Budget in millions"),
    must_include: Optional[str] = Query(None, description="Comma-separated driver IDs to include"),
    exclude: Optional[str] = Query(None, description="Comma-separated driver IDs to exclude"),
):
    """
    Get optimal team recommendation within budget.
    
    Uses optimization to maximize expected points.
    """
    predictor = get_fantasy_predictor()
    
    must_include_ids = []
    if must_include:
        try:
            must_include_ids = [int(x.strip()) for x in must_include.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid must_include format")
    
    exclude_ids = []
    if exclude:
        try:
            exclude_ids = [int(x.strip()) for x in exclude.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid exclude format")
    
    try:
        recommendation = predictor.recommend_team(
            budget=budget,
            must_include=must_include_ids,
            exclude=exclude_ids,
        )
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/value-plays", response_model=List[FantasyPrediction])
async def get_value_plays(
    limit: int = Query(10, ge=1, le=20, description="Number of value plays to return"),
):
    """
    Get best value plays (highest points per million).
    
    Returns drivers sorted by value metric.
    """
    predictor = get_fantasy_predictor()
    
    try:
        value_plays = predictor.get_value_plays(limit=limit)
        return value_plays
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{driver1_id}/{driver2_id}")
async def compare_drivers(
    driver1_id: int,
    driver2_id: int,
    circuit_id: Optional[str] = Query(None, description="Circuit identifier"),
):
    """
    Compare two drivers for fantasy purposes.
    
    Returns detailed comparison with recommendation.
    """
    predictor = get_fantasy_predictor()
    
    try:
        comparison = predictor.compare_drivers(
            driver1_id=driver1_id,
            driver2_id=driver2_id,
            circuit_id=circuit_id,
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/differential")
async def get_differential_picks(
    budget_after_core: float = Query(..., description="Remaining budget after core picks"),
):
    """
    Get differential picks for Fantasy F1.
    
    Differential picks are lower-owned drivers that could provide
    an advantage if they perform well.
    """
    predictor = get_fantasy_predictor()
    
    try:
        # Get all predictions
        all_predictions = []
        for driver_id in predictor.DRIVER_PRICES.keys():
            driver_name = f"Driver {driver_id}"
            team_name = predictor._get_team_for_driver(driver_id)
            pred = predictor.predict_points(driver_id, driver_name, team_name)
            all_predictions.append(pred)
        
        # Filter by budget and sort by upside potential
        differentials = [
            p for p in all_predictions
            if p.price <= budget_after_core
            and p.risk_level in ['medium', 'high']  # Higher risk = differential
        ]
        
        # Sort by points per million
        differentials.sort(key=lambda x: x.points_per_million, reverse=True)
        
        return {
            'differentials': differentials[:5],
            'budget': budget_after_core,
            'recommendation': differentials[0] if differentials else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prices")
async def get_all_prices():
    """
    Get all driver and constructor prices.
    
    Returns current Fantasy F1 prices.
    """
    predictor = get_fantasy_predictor()
    
    return {
        'drivers': predictor.DRIVER_PRICES,
        'constructors': predictor.CONSTRUCTOR_PRICES,
        'last_updated': '2024-01-01',  # TODO: Get from config
    }
