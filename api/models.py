from django.db import models
from django.contrib.auth.models import User

class FoodItem(models.Model):
    CATEGORY_CHOICES = [
        ('BREAKFAST', 'Breakfast'),
        ('LUNCH', 'Lunch'),
        ('SNACK', 'Snack'),
        ('DRINK', 'Drink'),
        ('DESSERT', 'Dessert'),
    ]
    DIET_CHOICES = [
        ('VEG', 'Vegetarian'),
        ('NON_VEG', 'Non-Vegetarian'),
        ('VEGAN', 'Vegan'),
    ]
    SPICE_CHOICES = [
        ('MILD', 'Mild'),
        ('MEDIUM', 'Medium'),
        ('SPICY', 'Spicy'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    diet_type = models.CharField(max_length=20, choices=DIET_CHOICES, blank=True, null=True)
    spice_level = models.CharField(max_length=20, choices=SPICE_CHOICES, blank=True, null=True)
    preparation_time = models.IntegerField(help_text="Preparation time in minutes")
    calories = models.IntegerField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    diet_type = models.CharField(max_length=20, choices=FoodItem.DIET_CHOICES, blank=True, null=True)
    min_budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    spice_preference = models.CharField(max_length=20, choices=FoodItem.SPICE_CHOICES, blank=True, null=True)
    max_preparation_time = models.IntegerField(blank=True, null=True, help_text="In minutes")
    
    favorite_categories = models.JSONField(default=list, blank=True)
    favorite_foods = models.JSONField(default=list, blank=True)
    allergies = models.JSONField(default=list, blank=True)
    foods_to_avoid = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences of {self.user.username}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    food = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'food'], name='unique_user_food_favorite')
        ]

    def __str__(self):
        return f"{self.user.username} favorites {self.food.name}"

class RecommendationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_history', null=True, blank=True)
    query = models.TextField()
    preferences = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list)
    selected_recommendation = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Recommendation for {self.user.username} at {self.created_at}"
        return f"Anonymous Recommendation at {self.created_at}"
