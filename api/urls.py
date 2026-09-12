from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register_user, login_user, get_profile, update_preferences,
    FoodItemViewSet, FavoriteViewSet, get_recommendation_history, get_recommendations
)

router = DefaultRouter()
router.register(r'foods', FoodItemViewSet)
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('profile/', get_profile, name='get_profile'),
    path('profile/preferences/', update_preferences, name='update_preferences'),
    path('recommendations/history/', get_recommendation_history, name='recommendation_history'),
    path('recommendations/', get_recommendations, name='get_recommendations'),
    path('', include(router.urls)),
]
