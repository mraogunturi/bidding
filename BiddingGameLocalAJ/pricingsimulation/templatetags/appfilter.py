__author__ = 'python'
from django import template
from datetime import date, timedelta
from pricingsimulation.models import *

register = template.Library()


@register.filter(name='quit')
def filter_users_joined_games(data):
    user_data = data.exclude(status="Q")
    return user_data


@register.filter(name='join')
def filter_users_joined_games(data):
    user_data = data.exclude(status="J")
    return user_data

@register.filter
def get_joined_user_count(game_id):
	if not game_id:
		return 0
	return UserGameRecords.objects.filter(game_id=game_id).count()

@register.filter
def multiply(value, arg):
    return value*arg


@register.filter
def get_nick_name(game_id, user_id):
	return UserGameRecords.objects.get(game_id=game_id, user_id=user_id).user_nick_name
