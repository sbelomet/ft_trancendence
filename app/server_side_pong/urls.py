from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameViewSet

# Initialize the router
router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')

urlpatterns = [
    path('', include(router.urls)),  # Include all routes registered in the router
]
