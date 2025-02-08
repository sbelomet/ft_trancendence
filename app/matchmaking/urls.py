from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TournamentInvitationViewSet, TournamentViewSet, PlayerViewSet, PlayerStatisticsViewSet, PlayerRankingViewSet, HistoryViewSet
from .tasks import launch_tournaments
from django.urls import re_path

# Routeur principal
router = DefaultRouter()
router.register(r'invitations', TournamentInvitationViewSet, basename='tournament-invitation')
router.register(r'tournaments', TournamentViewSet, basename='tournament')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'statistics', PlayerStatisticsViewSet, basename='statistics')
router.register(r'ranking', PlayerRankingViewSet, basename='ranking')


#utilisation de re_path car recherches dynamiques (avec regex)
#correspond à un appel comme : /players/<player_id>/history/<history_type>/
#players/ + /history/ sont fixes
#^ : fait commencer au début de l'url
#(?P<player_id>\d+) : récupère player_id qui doit être des chiffres (\d+).
#(?P<history_type>matches|tournaments) : récupre history_type qui doit être soit matches soit tournaments.
#/$ : indique la fin de l'url

urlpatterns = [
    path('', include(router.urls)),
	path('launch-tournaments/', launch_tournaments, name='launch-tournaments'),
	#path("statistics/<int:pk>/", PlayerStatisticsViewSet.as_view({"get": "retrieve"})),
	re_path(
        r'^players/(?P<player_id>\d+)/history/(?P<history_type>matches|tournaments)/$',
        HistoryViewSet.as_view({'get': 'list'}),
        name='player-history'
    ),
]


