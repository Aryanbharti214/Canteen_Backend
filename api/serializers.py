from rest_framework import serializers
from .models import FoodItem, UserPreference, Favorite, RecommendationHistory
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = '__all__'

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = '__all__'
        read_only_fields = ['user']

class FavoriteSerializer(serializers.ModelSerializer):
    food_detail = FoodItemSerializer(source='food', read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'food', 'food_detail', 'created_at']
        read_only_fields = ['user']

class RecommendationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationHistory
        fields = '__all__'
        read_only_fields = ['user']
