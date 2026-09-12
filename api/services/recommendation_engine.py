from decimal import Decimal
from typing import List, Dict, Any
import itertools
from api.models import FoodItem

def score_item(item, preferences: dict) -> int:
    score = 0
    # Base availability score
    if item.is_available:
        score += 10
        
    # Budget match (if under budget, gets max 30 pts)
    # The combination logic will handle exact budget checks, but individual items get scored too
    budget = preferences.get('budget')
    if budget:
        if item.price <= budget:
            score += 30
            
    # Diet match (20 points)
    diet_type = preferences.get('diet_type')
    if diet_type and item.diet_type == diet_type:
        score += 20
        
    # Spice match (15 points)
    spice_level = preferences.get('spice_level')
    if spice_level and item.spice_level == spice_level:
        score += 15
        
    # Time match (15 points)
    max_time = preferences.get('max_preparation_time')
    if max_time and item.preparation_time <= max_time:
        score += 15
        
    # Category / Mood match (10 points) - simple approximation
    mood = preferences.get('mood')
    if mood == 'HUNGRY' and item.category in ['LUNCH', 'BREAKFAST']:
        score += 10
        
    return score

def score_combination(combo: List[FoodItem], preferences: dict) -> dict:
    total_price = sum(item.price for item in combo)
    prep_time = max(item.preparation_time for item in combo) # concurrent prep
    
    combo_score = 0
    
    budget = preferences.get('budget')
    if budget:
        if total_price <= budget:
            combo_score += 30
    
    # Diet match: combo matches if all items match the diet (if specified)
    diet_type = preferences.get('diet_type')
    if diet_type:
        if all(item.diet_type == diet_type for item in combo):
            combo_score += 20
            
    # Spice match: check if ANY item matches the spice preference
    spice_level = preferences.get('spice_level')
    if spice_level:
        matching_spice = sum(1 for item in combo if item.spice_level == spice_level)
        if matching_spice > 0:
            combo_score += 15
        if matching_spice == len(combo) and len(combo) > 1:
            combo_score += 5 # Bonus if ALL items match the spice preference
            
    # Time match
    max_time = preferences.get('max_preparation_time')
    if max_time:
        if prep_time <= max_time:
            combo_score += 15
            
    # Availability
    if all(item.is_available for item in combo):
        combo_score += 10
        
    # Mood/Category
    mood = preferences.get('mood')
    if mood == 'HUNGRY':
        # If combo has at least one substantial item
        combo_score += 10

    reasons = []
    if budget and total_price <= budget:
        reasons.append(f"Within your ₹{budget} budget")
    if spice_level and any(item.spice_level == spice_level for item in combo):
        reasons.append(f"Matches your {spice_level.lower()} preference")
    if all(item.is_available for item in combo):
        reasons.append("Available now")
    if max_time and prep_time <= max_time:
        reasons.append(f"Can be prepared within {max_time} minutes")
        
    if not reasons:
        reasons.append("A good choice for you")

    return {
        "type": "combination" if len(combo) > 1 else "single",
        "items": [
            {"id": item.id, "name": item.name, "price": float(item.price)} for item in combo
        ],
        "total_price": float(total_price),
        "preparation_time": prep_time,
        "match_score": combo_score,
        "reasons": reasons
    }

def generate_recommendations(preferences: dict, all_foods) -> List[Dict[Any, Any]]:
    # Step 1: Remove unavailable items
    foods = [f for f in all_foods if f.is_available]
    
    # Step 2: Apply dietary restrictions (hard constraint)
    # If diet_type is VEG, remove NON_VEG
    diet_type = preferences.get('diet_type')
    if diet_type == 'VEG':
        foods = [f for f in foods if f.diet_type != 'NON_VEG']
    elif diet_type == 'VEGAN':
        foods = [f for f in foods if f.diet_type == 'VEGAN']
        
    # Step 4: Apply maximum preparation time (hard constraint for singles)
    max_time = preferences.get('max_preparation_time')
    
    # Step 5: Apply budget constraints (hard constraint for singles)
    budget = preferences.get('budget')
    
    # Valid single items
    valid_singles = []
    for f in foods:
        if max_time and f.preparation_time > max_time:
            continue
        if budget and f.price > budget:
            continue
        valid_singles.append(f)
        
    recommendations = []
    
    # Add valid singles
    for f in valid_singles:
        recommendations.append(score_combination([f], preferences))
        
    # Step 7: Generate combinations of two compatible food items
    # For combinations, we can use any available food, as long as the combo meets budget and time constraints
    for combo_tuple in itertools.combinations(foods, 2):
        combo = list(combo_tuple)
        
        # Check hard constraints on the combination
        total_price = sum(item.price for item in combo)
        prep_time = max(item.preparation_time for item in combo)
        
        if budget and total_price > budget:
            continue
        if max_time and prep_time > max_time:
            continue
            
        recommendations.append(score_combination(combo, preferences))
        
    # Step 8: Rank results by match_score descending, and then total_price descending (to favor combinations that utilize the budget well)
    recommendations.sort(key=lambda x: (x['match_score'], x['total_price']), reverse=True)
    
    return recommendations
