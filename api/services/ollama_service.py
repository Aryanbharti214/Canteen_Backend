import os
import requests
import json
from django.conf import settings

def generate_response(prompt):
    base_url = getattr(settings, 'OLLAMA_BASE_URL', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
    model = getattr(settings, 'OLLAMA_MODEL', os.getenv('OLLAMA_MODEL', 'qwen3:8b'))
    
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.RequestException as e:
        print(f"Ollama request failed: {e}")
        return None

def extract_preferences(query):
    prompt = f"""
Extract food preferences from this sentence.

Return ONLY valid JSON.

Fields:
budget (integer or null)
diet_type (string "VEG", "NON_VEG", "VEGAN" or null)
spice_level (string "MILD", "MEDIUM", "SPICY" or null)
mood (string or null)
max_preparation_time (integer or null)
category (string or null)
health_goal (string or null)

User:
"{query}"

Expected:
{{
  "budget": 80,
  "diet_type": null,
  "spice_level": "SPICY",
  "mood": "HUNGRY",
  "max_preparation_time": 15,
  "category": null,
  "health_goal": null
}}
"""
    response_text = generate_response(prompt)
    if response_text:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            print("Failed to decode JSON from Ollama.")
            return None
    return None

def generate_explanation(recommendation_text, preferences, query):
    prompt = f"""
You are a food recommendation assistant. Explain in one natural sentence why this recommendation was chosen based on the user's preferences.
Do NOT invent prices, change facts, or hallucinate. Use only the provided information. Do NOT return JSON.

User query: {query}
Parsed preferences: {preferences}
Recommendation to explain: {recommendation_text}

Explanation:
"""
    base_url = getattr(settings, 'OLLAMA_BASE_URL', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
    model = getattr(settings, 'OLLAMA_MODEL', os.getenv('OLLAMA_MODEL', 'qwen3:8b'))
    
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.RequestException as e:
        print(f"Ollama explanation request failed: {e}")
        return None
