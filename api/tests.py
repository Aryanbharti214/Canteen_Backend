from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from api.models import FoodItem
from api.services.preference_parser import fallback_parse
from api.services.recommendation_engine import generate_recommendations
from unittest.mock import patch

class CanteenAITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test food items based on the seed data
        FoodItem.objects.create(name="Chicken Roll", price=50, preparation_time=10, diet_type="NON_VEG", spice_level="SPICY", is_available=True)
        FoodItem.objects.create(name="Masala Fries", price=25, preparation_time=7, diet_type="VEG", spice_level="SPICY", is_available=True)
        FoodItem.objects.create(name="Idli Sambar", price=30, preparation_time=7, diet_type="VEG", spice_level="MILD", is_available=True)
        FoodItem.objects.create(name="Chicken Biryani", price=90, preparation_time=20, diet_type="NON_VEG", spice_level="SPICY", is_available=False)
        FoodItem.objects.create(name="Cold Coffee", price=40, preparation_time=5, diet_type="VEG", spice_level="MILD", is_available=True)

    # 1. Food API Test
    def test_food_api(self):
        response = self.client.get('/api/foods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    # 2. Food filtering test
    def test_food_filtering(self):
        response = self.client.get('/api/foods/', {'diet_type': 'VEG'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    # 3. Budget constraint test
    def test_budget_constraint(self):
        preferences = {"budget": 30}
        all_foods = list(FoodItem.objects.all())
        recommendations = generate_recommendations(preferences, all_foods)
        
        # Verify no recommendation exceeds 30
        for rec in recommendations:
            self.assertLessEqual(rec['total_price'], 30)
            
    # 4. Dietary constraint test
    def test_dietary_constraint(self):
        preferences = {"diet_type": "VEG"}
        all_foods = list(FoodItem.objects.all())
        recommendations = generate_recommendations(preferences, all_foods)
        
        for rec in recommendations:
            for item in rec['items']:
                food = FoodItem.objects.get(id=item['id'])
                self.assertEqual(food.diet_type, "VEG")

    # 5. Availability constraint test
    def test_availability_constraint(self):
        preferences = {"budget": 100} # Enough for biryani
        all_foods = list(FoodItem.objects.all())
        recommendations = generate_recommendations(preferences, all_foods)
        
        for rec in recommendations:
            for item in rec['items']:
                self.assertNotEqual(item['name'], "Chicken Biryani")

    # 6. Preparation time constraint test
    def test_preparation_time_constraint(self):
        preferences = {"max_preparation_time": 5}
        all_foods = list(FoodItem.objects.all())
        recommendations = generate_recommendations(preferences, all_foods)
        
        for rec in recommendations:
            self.assertLessEqual(rec['preparation_time'], 5)

    # 7. Combination recommendation test
    def test_combination_recommendation(self):
        preferences = {"budget": 80, "spice_level": "SPICY", "max_preparation_time": 15}
        all_foods = list(FoodItem.objects.all())
        recommendations = generate_recommendations(preferences, all_foods)
        
        top_rec = recommendations[0]
        # Should be Chicken Roll + Masala Fries = 75
        item_names = [i['name'] for i in top_rec['items']]
        self.assertIn("Chicken Roll", item_names)
        self.assertIn("Masala Fries", item_names)
        self.assertEqual(top_rec['total_price'], 75)

    # 8. Preference parser test (Fallback logic)
    def test_preference_parser_fallback(self):
        query = "I have ₹80, I'm hungry, want something spicy and only have 15 minutes."
        parsed = fallback_parse(query)
        self.assertEqual(parsed['budget'], 80)
        self.assertEqual(parsed['spice_level'], 'SPICY')
        self.assertEqual(parsed['max_preparation_time'], 15)
        self.assertEqual(parsed['mood'], 'HUNGRY')

    # 9. Ollama failure fallback test & 10. Recommendation API
    @patch('api.services.preference_parser.ollama_extract', return_value=None)
    def test_recommendation_api(self, mock_ollama):
        # When Ollama fails, it should use the fallback parser and still return 200
        data = {"query": "I have rs 80, I'm hungry, want something spicy and only have 15 minutes."}
        response = self.client.post('/api/recommendations/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        resp_data = response.data
        self.assertEqual(resp_data['parsed_preferences']['budget'], 80)
        
        top_rec = resp_data['recommendations'][0]
        self.assertEqual(top_rec['total_price'], 75)
        
        # Verify the history was created anonymously
        from api.models import RecommendationHistory
        self.assertEqual(RecommendationHistory.objects.count(), 1)
