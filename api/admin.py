from django.contrib import admin
from .models import FoodItem, UserPreference, Favorite, RecommendationHistory

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'diet_type', 'spice_level', 'preparation_time', 'is_available')
    list_filter = ('category', 'diet_type', 'spice_level', 'is_available')
    search_fields = ('name', 'description')

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'diet_type', 'min_budget', 'max_budget', 'spice_preference')
    search_fields = ('user__username',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'food', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'food__name')

@admin.register(RecommendationHistory)
class RecommendationHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'query')
