from enum import Enum
from typing import Dict, List
import re
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class HealthCategory(str, Enum):
    """Health categories for fact classification"""
    NUTRITION = "Nutrition"
    EXERCISE = "Exercise" 
    MENTAL_HEALTH = "Mental Health"
    WELLNESS = "Wellness"
    GENERAL = "General"  # Default fallback category

# Keywords for automatic category classification
CATEGORY_KEYWORDS: Dict[HealthCategory, List[str]] = {
    HealthCategory.NUTRITION: [
        # Food and diet
        "food", "diet", "nutrition", "eating", "meal", "calories", "vitamin", "mineral",
        "protein", "carbohydrate", "fat", "fiber", "sugar", "salt", "sodium", "calcium",
        "iron", "zinc", "antioxidant", "supplement", "nutrient", "organic", "processed",
        "vegetarian", "vegan", "gluten", "dairy", "fruit", "vegetable", "grain", "meat",
        "fish", "oil", "cooking", "recipe", "appetite", "hunger", "thirst", "digestion",
        "metabolism", "weight loss", "weight gain", "obesity", "malnutrition", "fasting",
        # Specific foods
        "apple", "banana", "spinach", "broccoli", "chicken", "salmon", "rice", "bread",
        "milk", "cheese", "yogurt", "nuts", "seeds", "beans", "water", "coffee", "tea",
        "alcohol", "wine", "beer", "chocolate", "honey", "sugar", "spice", "herb"
    ],
    
    HealthCategory.EXERCISE: [
        # Physical activity
        "exercise", "workout", "fitness", "training", "sport", "running", "walking",
        "jogging", "cycling", "swimming", "yoga", "pilates", "strength", "cardio",
        "aerobic", "anaerobic", "muscle", "endurance", "flexibility", "stretching",
        "gym", "weights", "lifting", "bodybuilding", "marathon", "athletic", "physical",
        "movement", "activity", "dance", "hiking", "climbing", "skiing", "tennis",
        "basketball", "football", "soccer", "baseball", "golf", "boxing", "martial",
        # Body parts and functions
        "heart rate", "pulse", "stamina", "recovery", "performance", "coordination",
        "balance", "posture", "joint", "bone", "ligament", "tendon", "injury", "strain"
    ],
    
    HealthCategory.MENTAL_HEALTH: [
        # Mental and emotional wellbeing
        "mental", "psychological", "emotional", "mood", "depression", "anxiety", "stress",
        "therapy", "counseling", "meditation", "mindfulness", "relaxation", "calm",
        "peace", "happiness", "joy", "sadness", "anger", "fear", "worry", "panic",
        "bipolar", "schizophrenia", "ptsd", "trauma", "grief", "loss", "addiction",
        "substance", "alcohol", "drug", "smoking", "brain", "cognitive", "memory",
        "concentration", "focus", "attention", "learning", "thinking", "behavior",
        "personality", "self-esteem", "confidence", "motivation", "resilience",
        "coping", "support", "social", "relationship", "family", "friend", "isolation",
        "loneliness", "suicide", "self-harm", "psychiatry", "psychology", "antidepressant"
    ],
    
    HealthCategory.WELLNESS: [
        # General health and wellness
        "wellness", "health", "healthy", "wellbeing", "lifestyle", "habit", "routine",
        "sleep", "rest", "fatigue", "energy", "tired", "insomnia", "dream", "nap",
        "hygiene", "cleanliness", "shower", "bath", "teeth", "dental", "oral", "skin",
        "hair", "beauty", "aging", "longevity", "immune", "immunity", "infection",
        "virus", "bacteria", "disease", "illness", "sick", "fever", "cold", "flu",
        "allergy", "asthma", "diabetes", "cancer", "heart", "blood", "pressure",
        "cholesterol", "stroke", "kidney", "liver", "lung", "stomach", "intestine",
        "hormone", "thyroid", "pregnancy", "birth", "baby", "child", "elderly",
        "prevention", "screening", "checkup", "doctor", "medicine", "treatment",
        "healing", "recovery", "pain", "headache", "migraine", "arthritis", "back",
        "spine", "posture", "ergonomic", "workplace", "environment", "air", "pollution",
        "smoking", "tobacco", "sunscreen", "uv", "radiation", "safety", "first aid"
    ]
}

def classify_health_claim(claim: str) -> HealthCategory:
    """
    Automatically classify a health claim into the most appropriate category
    using OpenAI GPT for intelligent classification.
    
    Args:
        claim: The health claim text to classify
        
    Returns:
        HealthCategory: The most appropriate category
    """
    if not claim:
        return HealthCategory.GENERAL
    
    # Try OpenAI classification first
    try:
        openai_category = _classify_with_openai(claim)
        if openai_category:
            return openai_category
    except Exception as e:
        print(f"OpenAI classification failed: {e}")
        # Fall back to keyword matching
        pass
    
    # Fallback to keyword-based classification
    return _classify_with_keywords(claim)

def _classify_with_openai(claim: str) -> HealthCategory:
    """
    Use OpenAI to classify the health claim into categories.
    """
    # Set up OpenAI client
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create the classification prompt
    prompt = f"""Classify this health claim into exactly one of these categories:

Categories:
- Nutrition: Food, diet, vitamins, supplements, eating habits, specific foods
- Exercise: Physical activity, fitness, sports, workouts, movement, physical training
- Mental Health: Stress, anxiety, depression, meditation, therapy, psychological wellbeing
- Wellness: General health, sleep, lifestyle, hygiene, disease prevention, medical care
- General: If it doesn't clearly fit the other categories

Health Claim: "{claim}"

Respond with ONLY the category name (Nutrition, Exercise, Mental Health, Wellness, or General)."""

    # Make the API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a health expert that classifies health claims into specific categories. Always respond with exactly one category name."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0.1
    )
    
    # Extract and validate the response
    category_name = response.choices[0].message.content.strip()
    
    # Map response to enum
    category_mapping = {
        "Nutrition": HealthCategory.NUTRITION,
        "Exercise": HealthCategory.EXERCISE,
        "Mental Health": HealthCategory.MENTAL_HEALTH,
        "Wellness": HealthCategory.WELLNESS,
        "General": HealthCategory.GENERAL
    }
    
    return category_mapping.get(category_name, HealthCategory.GENERAL)

def _classify_with_keywords(claim: str) -> HealthCategory:
    """
    Fallback keyword-based classification when OpenAI is unavailable.
    """
    if not claim:
        return HealthCategory.GENERAL
    
    # Convert to lowercase for matching
    claim_lower = claim.lower()
    
    # Count keyword matches for each category
    category_scores: Dict[HealthCategory, int] = {
        category: 0 for category in HealthCategory if category != HealthCategory.GENERAL
    }
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == HealthCategory.GENERAL:
            continue
            
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches = len(re.findall(pattern, claim_lower))
            category_scores[category] += matches
    
    # Find category with highest score
    best_category = max(category_scores.items(), key=lambda x: x[1])
    
    # Return best category if it has any matches, otherwise return GENERAL
    return best_category[0] if best_category[1] > 0 else HealthCategory.GENERAL

def get_category_display_name(category: HealthCategory) -> str:
    """Get the display name for a category (same as enum value)"""
    return category.value

def get_all_categories() -> List[str]:
    """Get all category names as strings"""
    return [category.value for category in HealthCategory]
