"""pricing URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import django.conf.urls
from django.contrib import admin
#from pricing import *
from pricingsimulation import views

# admin.autodiscover()

urlpatterns = [

    django.conf.urls.url(r'^$',  views.home),
    django.conf.urls.url(r'^login/',  views.user_authentication),
    django.conf.urls.url(r'^logout/',  views.user_session_end),
    # django.conf.urls.url(r'^registration/',  views.registration),
    django.conf.urls.url(r'^confirm/(?P<activation_key>\w+)/',  views.register_confirm),
    django.conf.urls.url(r'^Dashboard/',  views.dashboard),
    django.conf.urls.url(r'^get_dashboard_games/',  views.get_dashboard_games, name="get_dashboard_games"),
    django.conf.urls.url(r'^get_mydashboard_games/',  views.get_mydashboard_games, name="get_mydashboard_games"),
    django.conf.urls.url(r'^MyDashboard/',  views.user_dashboard),
    django.conf.urls.url(r'^get_game_timer/(?P<game_id>\d+)/(?P<turn_number>\d+)/', views.get_game_timer, name='get_game_timer'),
    django.conf.urls.url(r'^GameDetails/start_bidding_game/(?P<game_id>\d+)/', views.start_bidding_game, name='start_bidding_game'),
    django.conf.urls.url(r'^GameDetails/sameBidPlayerCount/(?P<game>\d+)/(?P<turn>\d+)/', views.get_turn_player_bid_count, name='get_turn_player_bid_count'),
    django.conf.urls.url(r'^GameDetails/players_count/(?P<game_id>\d+)/', views.players_count, name='players_count'),
    django.conf.urls.url(r'^GameDetails/current_player_count/(?P<game_id>\d+)/', views.current_player_count, name='current_players_count'),
    django.conf.urls.url(r'^GameDetails/results/(?P<game>\d+)/$', views.generate_results, name='generate_results'),
    django.conf.urls.url(r'^GameDetails/results/(?P<game>\d+)/show', views.game_results, name='game_results'),
    django.conf.urls.url(r'^GameDetails/results/winners/(?P<game>\d+)/', views.game_winners, name='game_winners'),
    django.conf.urls.url(r'^GameDetails/delete_game/(?P<game>\d+)/', views.delete_game, name='delete_game'),
    django.conf.urls.url(r'^GameDetails/',  views.game_details),
    # django.conf.urls.url(r'^Notification/',  views.Notification),
    django.conf.urls.url(r'^PlayGame/',  views.play_game),
    django.conf.urls.url(r'^TurnUpdate/', views.divturn_update ),
    django.conf.urls.url(r'^CreateGame/',  views.create_game),
    django.conf.urls.url(r'^moveturn/',  views.move_turn),
    django.conf.urls.url(r'^refresh_page/',  views.refresh_page),
    # django.conf.urls.url(r'^update_results/',  views.update_results),
    django.conf.urls.url(r'^next_turn_update/', views.update_turn_notify),
    django.conf.urls.url(r'^PlaceBid/', views.placeit_divturn_update),
    django.conf.urls.url(r'^download_results/', views.download_results),
    django.conf.urls.url(r'^admin/', admin.site.urls),
    django.conf.urls.url(r'^game-status/(?P<game_id>\d+)/', views.game_status, name='game_status'),

]


