from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from .models import FoodItem, UserPreference, Favorite, RecommendationHistory
from .serializers import (
    FoodItemSerializer, UserPreferenceSerializer, 
    FavoriteSerializer, RecommendationHistorySerializer, UserSerializer
)
from .services.preference_parser import parse_user_query
from .services.recommendation_engine import generate_recommendations
from .services.ollama_service import generate_explanation

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
    user = User.objects.create_user(username=username, password=password, email=email)
    UserPreference.objects.create(user=user)
    token, _ = Token.objects.get_or_create(user=user)
    
    return Response({'token': token.key, 'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UserSerializer(user).data})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_preferences(request):
    pref, _ = UserPreference.objects.get_or_create(user=request.user)
    serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FoodItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        'category': ['exact'],
        'diet_type': ['exact'],
        'price': ['lte'],
        'preparation_time': ['lte'],
        'is_available': ['exact']
    }
    search_fields = ['name', 'description']

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        food_id = self.request.data.get('food_id')
        try:
            food = FoodItem.objects.get(id=food_id)
            serializer.save(user=self.request.user, food=food)
        except FoodItem.DoesNotExist:
            raise serializers.ValidationError({"error": "Food item not found."})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recommendation_history(request):
    history = RecommendationHistory.objects.filter(user=request.user).order_by('-created_at')
    serializer = RecommendationHistorySerializer(history, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def get_recommendations(request):
    query = request.data.get('query')
    if not query:
        return Response({'error': 'Query is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    preferences = parse_user_query(query)
    
    if not preferences:
        return Response({'error': 'Failed to parse preferences.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    budget = preferences.get('budget')
    if budget is not None and budget <= 0:
        return Response({'error': 'Budget must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
        
    all_foods = list(FoodItem.objects.all())
    recommendations = generate_recommendations(preferences, all_foods)
    
    if not recommendations:
        return Response({
            "message": "No food matches all your requirements.",
            "alternatives": []
        }, status=status.HTTP_200_OK)
        
    best_recommendation = recommendations[0]
    
    explanation = generate_explanation(
        str(best_recommendation['items']), 
        str(preferences), 
        query
    )
    
    if explanation:
        best_recommendation['reasons'] = [explanation]
        
    alternatives = recommendations[1:4] if len(recommendations) > 1 else []

    if request.user.is_authenticated:
        RecommendationHistory.objects.create(
            user=request.user,
            query=query,
            preferences=preferences,
            recommendations=recommendations[:5]
        )
    else:
        RecommendationHistory.objects.create(
            user=None,
            query=query,
            preferences=preferences,
            recommendations=recommendations[:5]
        )
        
    return Response({
        "parsed_preferences": preferences,
        "recommendations": [best_recommendation],
        "alternatives": alternatives
    })
