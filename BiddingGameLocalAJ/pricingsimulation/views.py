import hashlib
import json
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core import serializers
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404,redirect
from django.utils import timezone
import socket
from django.core import serializers
from django.views.decorators.cache import cache_control
from django.db.models import Count
from .utils import *
from django.urls import reverse
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.template import Context, Template
from django.template import RequestContext
from django.template.loader import render_to_string
import random
import string
import logging
from collections import Counter

import pricing.actions as actions
from django.db import connection
import csv

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'login.html')


def user_authentication(request):
    if request.method == "POST":
        logger.info("%s:%d Begin User Authentication" %(request.session.session_key, time.time()))
        email = request.POST['email']
        
        EmailCheck = User.objects.filter(email=request.POST['email'])
        if email == '' :
            error = "Please Enter the Email Address."
            return render(request, 'login.html', {'error_message': error})

        
        if len(EmailCheck) == 0: # user registration
            print("user registered.")
            userData = User.objects.create_user(email, email)
            userData.set_password(settings.USER_PASSWORD)
            # userData.is_active = True
            userData.save()
            

        user = authenticate(username=email, password=settings.USER_PASSWORD)
        login(request, user)
        logger.info("%s:%d End User Authentication" % (request.session.session_key, time.time()))
        return HttpResponseRedirect('/Dashboard/')

    else:
        return render(request, 'login.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_session_end(request):
    logout(request)
    return render(request, 'login.html')


@transaction.atomic
def registration(request):
    if request.POST:
        email = request.POST['email']

        if email == '':
            error_message = "Please fill all the fields, all fields are mandatory."
            return render(request, 'registration.html', {'error_message': error_message})

        EmailAddressCheck = User.objects.filter(email=request.POST['email'])

        if len(EmailAddressCheck) > 0:
            mail = str(email)
            message = " %s , Email is Already Registered" % mail
            return render(request, 'registration.html', {'error_message': message})
        try:
                name = "{} {}".format(first_name, last_name)
                userData = User.objects.create_user(name, email, make_password(settings.USER_PASSWORD))
                # userData = User(first_name=first_name, last_name=last_name, username=email, email=email,
                #                 password=make_password(password), is_active=True)

                userData.save()
                
                print("user object is saved.")
                message = "Registration has been successful and verification email has been sent to %s." % mail
                return render(request, 'registration.html', {'success_message': message})
        except Exception as e:
            message = ""
            return render(request, 'registration.html', {'error_message': message})
            

    else:
        return render(request, 'registration.html')


def register_confirm(request, activation_key):
    # check if user is already logged in and if he is redirect him to some other url, e.g. home
    if request.user.is_authenticated():
        HttpResponseRedirect('/login/')

    # check if there is UserProfile which matches the activation key (if not then display 404)
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key)

    # check if the activation key has expired, if it has then render confirm_expired.html
    if user_profile.key_expires < timezone.now():
        return render(request, 'registration.html')
    # if the key hasn't expired save user and set him as active and render some template to confirm activation
    user = user_profile.user
    user.is_active = True
    user.save()
    message = "%s, Your account is confirmed and activated. Please login to website using your id and password." % user.first_name
    return render(request, 'login.html', {'success_message': message})


# def send_activation_mail(email, url, fname, lname):
#     from django.template.loader import get_template
#     from django.template import Context
#     from django.core.mail import EmailMultiAlternatives

#     plaintext = get_template('email_template_user_registration')
#     htmly = get_template('email.html')

#     date = datetime.datetime.today().strftime("%B %d, %Y")
#     d = Context({'date': date, 'url': url, 'fname': fname, 'lname': lname})

#     subject = "cre Account Activation"
#     from_email = ''
#     to = [email]
#     text_content = plaintext.render(d)
#     html_content = htmly.render(d)
#     msg = EmailMultiAlternatives(subject, text_content, from_email, to)
#     msg.attach_alternative(html_content, "text/html")
#     msg.send()
#     return True


def get_game_timer(request, game_id, turn_number, forceUpdate=False):
    
    print("game ID", game_id)
    # if int(turn_number) <= 1:
    #     remaining_time = 59
    #     return HttpResponse(JsonResponse({"remaining_time":remaining_time}), content_type="application/json")
    game_time_key = "elapsedTime{}{}".format(turn_number, game_id)
    print("game session: %s" % cache.get(game_time_key))
    print("game_key: %s" % game_time_key)
    elapsedTime = cache.get(game_time_key)
    print(cache, "cache_object")
    print("time in session " + str(elapsedTime))
    if (elapsedTime is None) or forceUpdate:
        remaining_time = 59
        elapsedTime = 0
        cache.set(game_time_key, time.time())
        # cache[game_time_key] = time.time()
    else:
        remaining_time = math.floor(time.time() - elapsedTime)
        print("remaining time: %s" % remaining_time)

        remaining_time = 59 - remaining_time 
        if remaining_time < 0:
            remaining_time = 0 

    print("remaining time: " + str(remaining_time))
    return HttpResponse(JsonResponse({"remaining_time":remaining_time}), content_type="application/json")


@login_required
def dashboard(request):

    #is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)

    games, usergames = actions.get_all_games(request.user.id)

    if 'playnow' in request.POST:
        print(request.POST)
        game_id = request.POST['game']
        mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
        user_rec = UserGameRecords.objects.filter(game_id=game_id, status='J')
        no_of_player = len(user_rec)
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        if game_data.game_status == "P":
            game_data.start_date_time = datetime.datetime.now()
            game_data.game_status = "S"
            # game_data.no_of_normal_players = no_of_player
            # game_data.number_of_players = game_data.no_of_normal_players + game_data.no_of_ai_player
            game_data.save()
            force_start(game_id)
        is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
        return render(request, 'dashboard.html', {'games': games, 'user_games': is_active_game})
    elif 'start_bidding' in request.POST:
        # If owner started the game from the dashboard without joining into the game.
        print ("User %s clicked on Start Game button" % request.user.email)
        game_id = request.POST['game']
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        if game_data.game_status == "P":
            game_data.start_date_time = datetime.datetime.now()
            game_data.game_status = "S"
            # game_data.no_of_normal_players = no_of_player
            # game_data.number_of_players = game_data.no_of_normal_players + game_data.no_of_ai_player
            game_data.save()
            cache.set("GameDetails%s"%game_id, game_data)
            push_turn_2(game_id)
            noted = Notify.objects.get(game_id=game_id)
            noted.msg = 'S'
            noted.save()
            #bid_player_count = BidValues.objects.filter(game_id=game_id, no_of_turn=1).count()
            games, user_games = actions.get_all_games(request.user.id)
            message = 'Game is waiting for bids. Please click on Next Turn after players has been bidded.'
            return render(request, 'dashboard.html',
                          {'games': games, 'user_games': user_games, 'error_message': message})

    elif 'next_turn' in request.POST:
        game_id = request.POST['game']
        game_data = cache.get("GameDetails%s" % game_id) or Game.objects.get(id=game_id)
        push_turn_2(game_id)
        bid_player_count = BidValues.objects.filter(game_id=game_id, no_of_turn=1).count()
        message = game_data.name+" game is running with %d players." %(bid_player_count)

        #games, user_games = actions.get_all_games(request.user.id)
        #message = 'Game is running with {0} players.'.format(bid_player_count)
        games = Game.objects.filter(is_active=True, start_date_time__gte=datetime.date.today()).exclude(
        game_status='E')
        user_active_games = UserGameRecords.objects.filter(user_id=request.user.id).values('game_id')
        user_games = [g['game_id'] for g in user_active_games]

        return render(request, 'dashboard.html',
                      {'games': games, 'user_games': user_games, 'error_message': message})

    elif 'join' in request.POST:
        print(request.POST)
        game_id = int(request.POST['game'])
        nick_name = request.POST['nick_name']
        is_active_game = UserGameRecords.objects.filter(user_id=request.user.id, status='J')
        if len(is_active_game) == 0:
            game = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
            if cache.get("GameDetails%s"%game_id) is None:cache.set("GameDetails%s"%game_id, game)
            UserGame = UserGameRecords()
            UserGame.game_id = game.id
            UserGame.user_id = request.user.id
            print("userGame", request.user.id)
            UserGame.status = 'J'
            UserGame.user_nick_name = nick_name
            print("user nick name:", nick_name)
            UserGame.save()
            message = "You have joined the game."
            return HttpResponseRedirect('/MyDashboard/')
        else:
            message = "You already joined game, please quit existing game to join new one."
            games, user_games = actions.get_all_games(request.user.id)
            return render(request, 'dashboard.html',
                          {'games': games, 'user_games': user_games, 'error_message': message})
    elif 'result' in request.POST:
        game = request.POST['game']

        game = Game.objects.get(id=game)
        if game.game_status == 'R':
            render(request, "result_status.html", {"game":game})


        bidval = WinnerTable.objects.filter(game_id=game)
        data = []
        for d in bidval:
            #syso("{Key:"+obj.value)
            data.append(
                {"net_con": d.player_total_net_contribution, "email": d.player.email, "rank": d.player_rank})

        fleet_info=FleetNetContribution.objects.filter(game_id=game).order_by('player_id')

        json_data = JsonResponse(data)
        logger.info("%s:%d Fetching simulation details for game id: %s" % (request.session.session_key, time.time(), game))
        mybid = GameSimulationDetails.objects.filter(game_id=game).order_by('player_id')
        logger.info("%s:%d Done Fetching simulation details for game id: %s" % (request.session.session_key, time.time(), game))
        data_bid = []
        logger.info("%s:%d Fetching Bid Values for game id: %s" % (request.session.session_key, time.time(), game))
        my_bidvalues = BidValues.objects.filter(game_id=game).order_by('player_id')
        logger.info("%s:%d Done Fetching Bid Values for game id: %s" % (request.session.session_key, time.time(), game))
        for d in my_bidvalues:
            if d.player.email in data_bid:
                data_dict = {'turn_data': [{'turn': d.no_of_turn, "valA2B": d.value_a2b, "valB2A": d.value_b2a}]}
            else:
                data_dict = {'email': d.player.email,
                             'turn_data': [{'turn': d.no_of_turn, "valA2B": d.value_a2b, "valB2A": d.value_b2a}]}
                data_bid.append(data_dict)
        #till here under test
        player_info=[]
        for d in mybid:
            myjson={d.player.email:[]}
            a={}
            a['turn']=d.no_of_turn
            a['valA2B']=d.value_a2b
            a['valB2A']=d.value_b2a
            myjson.get(d.player.email).append(a)
            # player_info.append({'turn': d.no_of_turn, "valA2B": d.value_a2b, "valB2A": d.value_b2a})
        # myjson=JsonResponse(myjson)
        json_bid_data = json.dumps(data_bid)
        is_result_generated = get_result(game)
        if not is_result_generated:
            message = ""
            return render(request, 'results.html',
                          {'game_id': game, 'bidval': bidval,'myjson':myjson ,"fleet_info":fleet_info,"json_bid_data": json_bid_data, 'json_data': json_data,
                           'data': data,
                           'mybid': mybid, 'error_message': message})
        else:
            winner_data = WinnerTable.objects.filter(game_id=game).order_by('player_rank')

            return render(request, 'results.html',
                          {'game_id': game, 'bidval': bidval,"fleet_info":fleet_info, "json_bid_data": json_bid_data,'myjson':myjson ,'json_data': json_data,"data_bid":data_bid,
                           'mybid': mybid,
                           'winner': winner_data})
    elif 'view' in request.POST or 'game' in request.POST:
        game_id = request.POST['game']
        games_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        return render(request, 'game_details.html', {'data': games_data})
    return render(request, 'dashboard.html', {'games': games, 'user_games': usergames })

def get_dashboard_games(request):
    games, user_games = actions.get_all_games(request.user.id)
    return render(request, 'components/dashboard_games_table.html', {'games': games, 'user_games': user_games})

def get_mydashboard_games(request):
    game_id = request.GET['game_id']
    # game_ids = game_ids if isinstance(game_ids, (list, tuple)) else [game_ids]
    #print("function get_maydashboard_games() - > game_id: %s" %game_id)
    try:
      game = Game.objects.get(is_active=True, id=game_id)
      userGame = UserGameRecords.objects.get(user_id=request.user.id, game_id=game_id)
    except Exception as e:
        game = None
        userGame = []

    return render(request, 'components/mydashboard_table.html', {'game':game, 'userGame':userGame})
    

def game_details(request):
    print(request.POST, 'posted data')
    if 'view' in request.POST:
        game_id = request.POST['game']
        games_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        return render(request, 'game_details.html', {'data': games_data})
    elif 'join' in request.POST:
        games = request.POST['game']
        is_active_game = UserGameRecords.objects.filter(user_id=request.user.id, status='J')
        if len(is_active_game) == 0:
            game = cache.get("GameDetails%s"%games) or Game.objects.get(id=games)
            UserGame = UserGameRecords()
            UserGame.game_id = game.id
            UserGame.user_id = request.user.id
            UserGame.status = 'J'
            UserGame.save()
            message = "You have joined the game."
            games = Game.objects.filter(is_active=True).exclude(game_status='E')
            is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
            usergames = []
            for id in is_active_game:
                usergames.append(id.game_id)
            return render(request, 'mydashboard.html', {'games': games, 'user_games': is_active_game, })
                          # {'games': games, 'user_games': usergames, 'success_message': message})
        else:
            message = "You already joined game, please quit existing game to join new one."
            games = Game.objects.filter(is_active=True).exclude(game_status='E')
            is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
            usergames = []
            for id in is_active_game:
                usergames.append(id.game_id)
            return render(request, 'mydashboard.html',
                          {'games': games, 'user_games': usergames, 'error_message': message})

    elif 'quit' in request.POST:
        print("User %s clicked the Quit button in My Game Page" %request.user.email)
        game = request.POST['game']
        is_active_game = UserGameRecords.objects.get(game_id=game, user_id=request.user.id)
        updateUserGame = UserGameRecords.objects.get(id=is_active_game.id)
        updateUserGame.status = 'Q'
        updateUserGame.save()
        # UserGameRecords.objects.get(id=is_active_game.id).delete()
        #games = Game.objects.filter(is_active=True).exclude(game_status='E')
        games = Game.objects.filter(is_active=True)
        message = "You quit the game successfully."
        is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
        if 'redirect_to_results' in request.POST:
            #import time
            #time.sleep(1)
            #return HttpResponseRedirect(reverse('game_results', args=(game,)))
            return HttpResponseRedirect("/GameDetails/results/%s/" %str(game).strip())
        return render(request, 'mydashboard.html',
                      {'games': games, 'user_games': is_active_game, 'success_message': message})

    elif 'quitai' in request.POST:

        game_id = request.POST['game']
        is_active_game = UserGameRecords.objects.filter(game_id=game_id, status='T').update(status='Q')

        games = Game.objects.filter(is_active=True)
        message = "You quit the game successfully."
        is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
        return render(request, 'mydashboard.html',
                      {'games': games, 'user_games': is_active_game, 'success_message': message})
    elif 'result' in request.POST:
        game = request.POST['game']
        return HttpResponseRedirect("/GameDetails/results/%s/" %str(game).strip())
        # games = cache.get("GameDetails%s"%game) or Game.objects.get(id=game)
        #
        #
        # turn_limit=games.no_of_turns_per_player
        # bidval = WinnerTable.objects.filter(game_id=game).distinct()
        # bidval = []
        # for w in winner_data:
        #     if w.player_rank in bidval:
        #         w.delete()
        #         continue
        #     bidval.append(w.player_rank)

        # data = []  # [{'email':{turn:[a2b,b2a]}}]
        # for d in bidval:
        #     # data.append({d.player.email: {d.no_of_turn: [d.value_a2b, d.value_b2a]}})
        #     data.append(
        #         {"net_con": d.player_total_net_contribution, "email": d.player.email, "rank": d.player_rank})
        #
        # json_data = json.dumps(data)
        # mybid = GameSimulationDetails.objects.filter(game_id=game).order_by('no_of_turn')
        # data_bid = []

        # for m in mybid:
        #     data_bid.append({"turn_no":m.no_of_turn,"email":m.player.email,"valuea2b":m.value_a2b,"valueb2a":m.value_b2a,"award_value_a2b":m.trucks_a2b_Awarded,"award_value_b2a":m.trucks_b2a_Awarded,"turn_limit":turn_limit})
        # print("This is data bid")

        json_bid_data = json.dumps(data_bid)
        # is_result_generated = get_result(game)
        # if not is_result_generated:
        #     message = ""
        #     return render(request, 'results.html',
        #                   {'game_id': game, 'bidval': bidval, "json_bid_data": json_bid_data, 'turn_limit':turn_limit, 'data': data,
        #                    'mybid': mybid, 'error_message': message})
        # else:
        #     winner_data = WinnerTable.objects.filter(game_id=game).distinct().order_by('player_rank')
        #     # ranks = []
        #     # for w in winner_data:
        #     #     if w.player_rank in ranks:
        #     #         w.delete()
        #     #         continue
        #     #     ranks.append(w.player_rank)
        #     return render(request, 'results.html',
        #                   {'game_id': game, 'bidval': bidval,'turn_limit':turn_limit, "json_bid_data": json_bid_data,
        #                    'mybid': mybid,
        #                    'winner': winner_data})
    else:
        print("in else of dashboradr")

        return HttpResponseRedirect('/MyDashboard/')

def get_turn_player_bid_count(request, game, turn):
    turn = int(turn)
    same_turn_paritcipants = BidValues.objects.filter(game_id=game, no_of_turn=turn).count()
   # logger.debug("same_turn_paritcipants: ", same_turn_paritcipants)
    # print("turn: ", type(turn))
    if turn == 1:
        number_of_players = UserGameRecords.objects.filter(game_id=game).count()
    #    logger.debug("number of payer jonied: ", number_of_players)
    else:
        get_game_data = cache.get("GameDetails%s"%game) or Game.objects.get(id=game)
        number_of_players = get_game_data.number_of_players
    # print("number_of_players:" , number_of_players)
    message = {"number_of_player_bidded": same_turn_paritcipants, 
                "total_players": number_of_players}
    return HttpResponse(json.dumps(message), content_type="application/json")

def players_count(request, game_id):
    #print ("Players count " + game_id)
    joined_count = UserGameRecords.objects.filter(game_id=game_id).count()
    return HttpResponse(json.dumps({'total_palyers': joined_count}), content_type="application/json")

def current_player_count(request, game_id):
    players_count = UserGameRecords.objects.filter(game_id=game_id, status__in = ['B', 'T']).count()
    return HttpResponse(json.dumps({'total_palyers': players_count}), content_type="application/json")

def game_winners(request, game):
    games=cache.get("GameDetails%s"%game) or Game.objects.get(id=game)
    winner_data = WinnerTable.objects.filter(game_id=game).order_by('player_rank')
    return render(request, 'components/results_ranks.html',
                      {'game_id': game, 'winner': winner_data})


def generate_results(request, game):
    logger.info("Results requested by %s at %s" %(request.user.username, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")) )
    g = Game.objects.get(id = game)
    if g.game_status == 'S':
        g.game_status = "R"
        g.save()
        print("Redirecting to Game Results page")
        return HttpResponseRedirect("/GameDetails/results/%d/show" % g.id)
    elif g.game_status == 'E':
        return HttpResponseRedirect("/GameDetails/results/%d/show" %g.id)

    return render(request, "result_status.html", {"game": g})

def game_results(request, game):

    games = Game.objects.get(id=game)
    print("games.game_status")

    # if games.game_status == 'R':
    #    render(request, "result_status.html", {"game": games})

    logger.info("%s:%d Begin generating Result for game id: %s" % (request.session.session_key, time.time(), game))
    start_time = time.time()
    print("in result s view")
    #games=cache.get("GameDetails%s"%game) or Game.objects.get(id=game)

    turn_limit=games.no_of_turns_per_player
    bidval = WinnerTable.objects.filter(game_id=game).distinct()

    data = []  # [{'email':{turn:[a2b,b2a]}}]
    for d in bidval:
        # data.append({d.player.email: {d.no_of_turn: [d.value_a2b, d.value_b2a]}})

        data.append(
            {"net_con": d.player_total_net_contribution, "email": d.user_nick_name, "rank": d.player_rank})

    json_data = json.dumps(data)
    mybid = GameSimulationDetails.objects.filter(game_id=game).order_by('no_of_turn')
    data_bid = []
    
    for m in mybid:
        nick_name = UserGameRecords.objects.get(game_id=game, user_id=m.player.id).user_nick_name
        data_bid.append({"turn_no":m.no_of_turn,"email":nick_name,"valuea2b":m.value_a2b,"valueb2a":m.value_b2a,"award_value_a2b":m.trucks_a2b_Awarded,"award_value_b2a":m.trucks_b2a_Awarded,"turn_limit":turn_limit})

    print("This is data bid")

    json_bid_data = json.dumps(data_bid)
    is_result_generated = get_result(game)
    results = []
    player_dict = {}
    for b in mybid:
        if b.player_id not in player_dict:
            b.cumulative = b.net_contribution
            player_dict[b.player_id] = b.net_contribution
        else:
            player_dict[b.player_id] = player_dict[b.player_id] + b.net_contribution
            b.cumulative = player_dict[b.player_id]

        results.append(b)

    mybid = results

    if not is_result_generated:
        message = ""
        logger.info("%s:%d Done generating results for game id: %s in %f seconds" % (
            request.session.session_key, time.time(), game, time.time() - start_time))
        return render(request, 'results.html',
                      {'game_id': game, 'bidval': bidval, "json_bid_data": json_bid_data, 'turn_limit':turn_limit, 'data': data,
                       'mybid': mybid, 'error_message': message})
    else:
        winner_data = WinnerTable.objects.filter(game_id=game).distinct().order_by('player_rank')
        ranks = []
        for w in winner_data:
            if any([i for i in ranks if i.player_rank == w.player_rank]):
                w.delete()
                continue
            ranks.append(w)
        logger.info("%s:%d Done generating results for game id: %s in %f ms" % (
            request.session.session_key, time.time(), game, time.time() - start_time))

        return render(request, 'results.html',
                      {'game_id': game, 'bidval': ranks,'turn_limit':turn_limit, "json_bid_data": json_bid_data,
                       'mybid': mybid,
                       'winner': ranks})

def user_dashboard(request):
    # quit_messages = []
    # user_joined_qui_games = UserGameRecords.objects.filter(~Q(status='Q'), game_id__game_status='E', user_id=request.user.id)
    # for user_game in user_joined_qui_games:
    #     # user_game.status = 'Q'
    #     # user_game.save()
    #     quit_messages.append('You quit "{}" game successfully'.format(user_game.game.name))
    # print('success_message': '. '.join(quit_messages))
    #games = Game.objects.filter(is_active=True).exclude(game_status='E').order_by('-created_date')
    games = Game.objects.filter(is_active=True).order_by('-created_date')
    is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
    return render(request, 'mydashboard.html', {'games': games, 'user_games': is_active_game})

def randomword(name_length=10):
    start = 'AI'
    end = ''.join(random.choices(string.ascii_uppercase + string.digits, k=name_length-2))
    return "{}{}".format(start, end)


@login_required
def create_game(request):
    if request.POST:
        game_name = request.POST['game_name']
        start_date_time = datetime.datetime.now() #+datetime.timedelta(days=1)
        # sdt = datetime.datetime.strptime(start_date_time, '%m-%d-%y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S.%f')
        end_date_time = datetime.datetime.now()+ datetime.timedelta(days=2)
        #edt = datetime.datetime.strptime(end_date_time, '%m-%d-%y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S.%f')
        is_ai_true = request.POST.get('ai_check_flag', False)
        no_ai_players = int(request.POST['ai_limit'])
        #game_status = request.POST['game_status']
        player_limit = int(request.POST['player_limit'])
        turn_limit = request.POST['turn_limit']
        truck_limit = request.POST['truck_limit']
        brokerage_fee = request.POST['brokerage_fee']
        print("brokerage_fee:   ", brokerage_fee)
        #shrink_ratio = request.POST['shrink_ratio']
        #growth_ratio = request.POST['growth_ratio']
        empty_cost_pertruck = request.POST['empty_cost_pertruck']
        load_cost_pertruck = request.POST['load_cost_pertruck']
        unusedCapital_cost_pertruck = request.POST['unusedCapital_cost_pertruck']
        # total_trucksA2b=int(number_of_players)*int(truck_limit)*95/100
        number_of_players = player_limit + no_ai_players

        print("no_of_ai_players", no_ai_players)
        print("player_limit", player_limit)
        print("number of players", number_of_players)
        total_trucksA2b = int(number_of_players) * int(truck_limit) * 95 / 100
        total_trucksB2a = int(number_of_players) * int(truck_limit) * 75 / 100
        if is_ai_true:
            create_game_model = Game(user_id=request.user.id,
                                     name=game_name,
                                     start_date_time=start_date_time,
                                     end_date_time=end_date_time,
                                     #game_status=game_status,
                                     number_of_players=number_of_players,
                                     no_of_trucks=truck_limit,
                                     no_of_turns_per_player=turn_limit,
                                     #shrink_ratio=shrink_ratio,
                                     #growth_ratio=growth_ratio,
                                     empty_cost_per_truck=empty_cost_pertruck,
                                     loaded_cost_per_truck=load_cost_pertruck,
                                     total_trucks_AvailableA2B=total_trucksA2b,
                                     total_trucks_AvailableB2A=total_trucksB2a,
                                     unused_capital_cost_perTruck=unusedCapital_cost_pertruck,
                                     is_ai=is_ai_true,
                                     no_of_normal_players=player_limit,
                                     no_of_ai_player=no_ai_players,
                                     brokerage_fee=brokerage_fee)
            create_game_model.save()
            notify=Notify()
            notify.game_id=create_game_model.id
            notify.save()


            total_ai_players = []  # [2,3,4]
            free_ai_players = []
            get_total_ai_players = UserProfile.objects.filter(is_ai_player=True)
            for ai in get_total_ai_players:
                total_ai_players.append(ai.user_id)

            # Collecting available AI Players from the existing AI Players
            for ai in total_ai_players:
                # noinspection PyBroadException
                try:
                    db_obj = UserGameRecords.objects.get(user_id=ai, status='J').user_id
                    if db_obj == ai:
                        pass
                except:
                    free_ai_players.append(ai)

            count = 0

            # Alloting available player to the newly created game.
            for ai in free_ai_players:
                if count == int(no_ai_players):
                    pass
                else:
                    db_obj_update = UserGameRecords(game_id=create_game_model.id, user_id=ai, status='J',
                                                    user_nick_name="AI player-%d" %ai)
                    db_obj_update.save()
                    count += 1

            # If available players are not sufficient to the total number of players required to the game
            # creating AI Player and assigining to the current game as user 'Joined'
            remaining_players = int(no_ai_players) - count
            if remaining_players > 0:

                for no in range(remaining_players):
                    username = randomword(10)
                    e = username + "@gmail.com"
                    user, created = User.objects.get_or_create(username=username, email=e, first_name="AI",
                                                               last_name="Player", is_active=True)
                    if created:
                        user.username = "AIPlayer-%d" %user.id
                        user.save()
                        userProfileData = UserProfile()
                        userProfileData.user_id = user.id
                        userProfileData.is_ai_player = True
                        userProfileData.save()
                        db_obj_update = UserGameRecords(user_nick_name="AI player-%d" %user.id, game_id=create_game_model.id, user_id=user.id, status='J')
                        db_obj_update.save()
                    else:
                        pass

            else:
                return HttpResponseRedirect('/Dashboard/')

            return HttpResponseRedirect('/Dashboard/')
        elif number_of_players < 2  :
            error_message="Number of players shoudn't be less then 2"
            return render(request,'create_game.html',{'error_message':error_message})
        elif game_name=='' :
            error_message="The Game name cannot be blank"
            return render(request,'create_game.html',{'error_message':error_message})
        else:
            no_ai_players=0
            number_of_players = player_limit

            create_game_model = Game(user_id=request.user.id,
                                     name=game_name,
                                     start_date_time=start_date_time,
                                     end_date_time=end_date_time,
                                     number_of_players=number_of_players,
                                     no_of_trucks=truck_limit,
                                     no_of_turns_per_player=turn_limit,
                                     empty_cost_per_truck=empty_cost_pertruck,
                                     loaded_cost_per_truck=load_cost_pertruck,
                                     total_trucks_AvailableA2B=total_trucksA2b,
                                     total_trucks_AvailableB2A=total_trucksB2a,
                                     unused_capital_cost_perTruck=unusedCapital_cost_pertruck,
                                     is_ai=is_ai_true,
                                     no_of_normal_players=player_limit,
                                     no_of_ai_player=no_ai_players,
                                     brokerage_fee=brokerage_fee)
            create_game_model.save()
            notify = Notify()
            notify.game_id = create_game_model.id
            notify.save()
            success_message="Your game is created"
            return HttpResponseRedirect('/Dashboard/')
    else:
        error_message = "Something went wrong"
        return render(request, 'create_game.html')


def randomword(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


def get_result(game):

    start_time = time.time()
    is_check_result = WinnerTable.objects.filter(game_id=game)
    if len(is_check_result) == 0:
        all_data = GameSimulationDetails.objects.filter(game_id=game)
        user_id = []
        user_total = dict()
        get_max = {}
        for player in all_data:
            if player.player_id not in user_id:
                user_id.append(player.player_id)

        # for userid in user_id:
        #     check_all_user_quit = UserGameRecords.objects.get(game_id=game, user_id=userid)
        #     if check_all_user_quit.status != 'Q':
        #         return False
        #     else:
        #         user_total[userid] = []
        #         get_total_sum_all_player = GameSimulationDetails.objects.filter(game_id=game, player_id=userid)
        #         for total in get_total_sum_all_player:
        #             user_total[userid].append(int(total.net_contribution))

        UserGameRecords.objects.filter(game_id=game, user_id__in=user_id).update(status='Q')
        game_sim_detail_list = GameSimulationDetails.objects.filter(game_id=game, player_id__in=user_id)
        for gs in game_sim_detail_list:
            if gs.player_id in user_total:
                user_total[gs.player_id].append(gs.net_contribution)
            else:
                user_total[gs.player_id] = [gs.net_contribution]

        # for userid in user_id:
        #     #check_all_user_quit = UserGameRecords.objects.get(game_id=game, user_id=userid)
        #     #if check_all_user_quit.status != 'Q':
        #     #    check_all_user_quit.status = 'Q'
        #     #    check_all_user_quit.save()
        #     #    #return False
        #
        #     user_total[userid] = []
        #     get_total_sum_all_player = GameSimulationDetails.objects.filter(game_id=game, player_id=userid)
        #     for total in get_total_sum_all_player:
        #         user_total[userid].append(int(total.net_contribution))

        for user, value in user_total.items():
            get_max[user] = sum(value)


        sort_rank = Counter(get_max).most_common()
        rank = 0
        # for player,total in get_max.items():
        get_game_id = cache.get("GameDetails%s"%game) or Game.objects.get(id=game)
        user_rank_list = [r[0] for r in sort_rank]
        user_nick_name_dict = {}
        winner_table_dict = {}

        ugr_query_set = UserGameRecords.objects.filter(game_id=game, user_id__in=user_rank_list)
        for ugr in ugr_query_set:
            user_nick_name_dict[(ugr.game_id, ugr.user_id)] = ugr.user_nick_name

        wt_query_set = WinnerTable.objects.all()
        for wt in wt_query_set:
            winner_table_dict[(wt.game_id, wt.player_id)] = 1

        winner_list = []
        for ranking in sort_rank:
            rank += 1
            winnerData = WinnerTable()
            #get_user_id = User.objects.get(id=ranking[0])
            user_id = ranking[0]
            
            winnerData.game_id = get_game_id.id
            winnerData.player_id = user_id
            winnerData.player_total_net_contribution = ranking[1]
            winnerData.player_rank = rank
            #winnerData.user_nick_name = UserGameRecords.objects.get(game_id=game, user_id=user_id).user_nick_name
            winnerData.user_nick_name = user_nick_name_dict[(get_game_id.id, user_id)]
            #if not WinnerTable.objects.filter(game_id=get_game_id.id, player_id=user_id):

            if (get_game_id.id, user_id) not in winner_table_dict:
                #winnerData.save()
                winner_list.append(winnerData)

        WinnerTable.objects.bulk_create(winner_list)
        g = Game.objects.get(id=game)
        g.game_status = 'E'
        g.save()
        logger.info("Results has been generated in %f sec for game_id: %d" %(time.time() - start_time, g.id))
        # print(max(get_max.keys(), key=(lambda user: get_max[user])))
        return True
    else:
        g = Game.objects.get(id = game)
        g.game_status = 'E'
        g.save()
        return True


def play_game(request):
    error_message, success_message,  = "", ""
    # When user clicked "Play Game" button after Game has been started.
    print ("function play_game()")
    if 'play' in request.GET:
        print ("User %s clicked on Play Game button" %request.user.email)
        game_id = request.GET['game']
        print("requet get", game_id)

        mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        total_player_count = game_data.number_of_players
        if game_data.game_status == "S":
            no_of_turns_of_game = game_data.no_of_turns_per_player
            total_finished_turns = BidValues.objects.filter(game_id=game_id, player_id=request.user.id)
            get_turn_count = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
            if get_turn_count.status == 'Q':
                # logger.debug("player removed from bidding.")
                message = "This game is already started. Please join in another game."
                #return HttpResponseRedirect(reverse('game_results', args=[game_id]))
                is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
                games = Game.objects.filter(is_active=True).exclude(game_status='E')
                return render(request, 'mydashboard.html',
                              {'games': games, 'user_games': is_active_game, 'success_message': message})

            if get_turn_count.no_of_turns_completed > 0:
                get_turn_count.status = get_turn_count.status
                get_turn_count.save()
            else:
                get_turn_count.status = 'B'
                get_turn_count.save()
            my_turn = get_turn_count.no_of_turns_completed
            if len(total_finished_turns) == no_of_turns_of_game:
                message = "This game is over, you cannot bid anymore. You can quit this game to join to new game."
                return HttpResponseRedirect(reverse('game_results', args=[game_id]))
                #return render(request, 'play_game.html', {'game_id': game_id, 'mybid': mybid, 'error_message': message})
            # elif len(mybid) != 0:
            #     return render(request, 'play_game.html',
            #                   {'game_id': game_id, 'mybid': mybid, 'turn': my_turn, 'game_data': game_data})
            else:
                print("requet get started ", game_id)
                print("turn count sent: %s" % my_turn)

                print("total_player_count : %s" % total_player_count)
                # import sys
                # sys.exit(1)
                return render(request, 'play_game.html',
                              {'game_id': game_id, 'turn': my_turn, 'mybid': mybid, 'game_data': game_data, 'total_player_count':total_player_count})
        else:
            print("request get not started", game_id)
            games = Game.objects.filter(is_active=True).exclude(game_status='E')
            is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
            message = "This game is not started yet."
            print(message)

            return render(request, 'mydashboard.html',
                          {'games': games, 'user_games': is_active_game, 'error_message': message})
    elif 'delete_game' in request.GET:
        print ("User %s clicked on Delete Game button" % request.user.email)
        game = request.GET['game']
        error_message = ""
        success_message = ""
        if game.user.id == request.user.id:
            print("in delete game: ", request.GET)
            UserGameRecords.objects.filter(game_id=game).update(status='Q')
            Game.objects.filter(id = game).update(game_status = 'E')
            success_message = "This game is deleted.."
            return HttpResponseRedirect(reverse('game_results', args=[game]))
        else:
            games = Game.objects.filter(is_active=True).exclude(game_status='E')
            is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
            message = "You are not alloed to delete the game."
            return render(request, 'mydashboard.html',
                          {'games': games, 'user_games': is_active_game, 'error_message': message})

    # When user clicked on Start Game button.
    elif 'playi' in request.GET:
        print ("User %s clicked on Start Game button" % request.user.email)
        game_id = request.GET['game']
        #mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
        user_rec = UserGameRecords.objects.filter(game_id=game_id, status='J')
        #no_of_player = len(user_rec)
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        if game_data.game_status == "P":
            game_data.start_date_time = datetime.datetime.now()
            game_data.game_status = "S"
            # game_data.no_of_normal_players = no_of_player
            # game_data.number_of_players = game_data.no_of_normal_players + game_data.no_of_ai_player
            game_data.save()
            cache.set("GameDetails%s"%game_id, game_data)
            force_start(game_id)

        games = Game.objects.filter(is_active=True).exclude(game_status='E').order_by('-created_date')
        message=game_data.name+" game is started, Click on play game to play"
        is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
        return render(request, 'mydashboard.html', {'games': games,'success_message':message, 'user_games': is_active_game})

    elif request.is_ajax():
        print ("Received Ajax Request from the User %s in play_game() function" %request.user.email)
        game_id = request.POST['game_id']
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
        if get_user_turn.no_of_turns_completed == game_data.no_of_turns_per_player:
            message = "This game is over you cannot bid anymore."
            mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
            return HttpResponse(json.dumps(message), content_type="application/json")
        elif get_user_turn.no_of_turns_completed == 1 and get_user_turn.status == 'I':
            print ("User %s is waiting for the second turn to start in play_game() function" % request.user.email)
            message = "Please wait for the second turn to start."
            mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
            return HttpResponse(json.dumps(message), content_type="application/json")
        else:
            if get_user_turn.no_of_turns_completed == 0 and get_user_turn.status == 'B':
                a2b = int(request.POST['a2b'])
                b2a = int(request.POST['b2a'])
                bid_value_obj = BidValues()
                bid_value_obj.game_id = game_data.id
                bid_value_obj.player_id = request.user.id
                bid_value_obj.value_a2b = a2b
                bid_value_obj.value_b2a = b2a
                bid_value_obj.no_of_turn = get_user_turn.no_of_turns_completed + 1
                if not BidValues.objects.filter(game_id=game_data.id,no_of_turn=bid_value_obj.no_of_turn,
                    player_id=request.user.id).count():
                    bid_value_obj.save()

                update_user = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                update_user.status = 'I'
                update_user.no_of_turns_completed += 1
                update_user.save()
                message = "Your bid has been places successfully."
                #mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                return HttpResponse(json.dumps(message), content_type="application/json")
            elif get_user_turn.no_of_turns_completed >= 1 and get_user_turn.status == 'T':
                a2b = int(request.POST['a2b'])
                b2a = int(request.POST['b2a'])
                bid_value_obj = BidValues()
                bid_value_obj.game_id = game_data.id
                bid_value_obj.player_id = request.user.id
                bid_value_obj.value_a2b = a2b
                bid_value_obj.value_b2a = b2a
                bid_value_obj.no_of_turn = get_user_turn.no_of_turns_completed + 1
                if not BidValues.objects.filter(game_id=game_data.id,no_of_turn=bid_value_obj.no_of_turn,
                    player_id=request.user.id).count():
                    bid_value_obj.save()
                update_user = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                update_user.no_of_turns_completed += 1
                update_user.save()
                #get_completed_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                get_completed_turn = update_user
                if get_completed_turn.no_of_turns_completed == game_data.no_of_turns_per_player:
                    #UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                    get_completed_turn.status = 'Q'
                    get_completed_turn.save()
                    success_message = "Your bid has been places successfully."
                    error_message = "This game is over you cannot bid anymore."
                    #mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                    return HttpResponse(json.dumps(success_message), content_type="application/json")
                else:
                    mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                    success_message = "Your bid has been places successfully."
                    return HttpResponse(json.dumps(success_message, mybid), content_type="application/json")
        return render(request, 'play_game.html', {'game_id': game_id})
    elif 'start_bidding' in request.GET:
        # Start without me button clicked
        game_id = request.GET['game']
        push_turn_2(game_id)
        noted = Notify.objects.get(game_id=game_id)
        noted.msg = 'S'
        noted.save()
        bid_player_count = BidValues.objects.filter(game_id=game_id, no_of_turn=1).count()
        try:
            BidValues.objects.get(game_id=game_id,no_of_turn=1,player_id=request.user.id)
        except BidValues.DoesNotExist:
            UserGameRecords.objects.filter(game_id=game_id, user_id=request.user.id).update(status='Q')
            print("owner game ended.")
        success_message = 'Game Started With {0} players.'.format(bid_player_count)


    games = Game.objects.filter(is_active=True).exclude(game_status='E')
    is_active_game = UserGameRecords.objects.filter(user_id=request.user.id)
    return render(request, 'mydashboard.html', {'games': games, 'user_games': is_active_game, 
                'error_message':error_message, 'success_message':success_message})

def delete_game(request, game):
    print ("User %s deleting game in delete_game() function" % request.user.email)
    error_message = ""
    success_message = ""
    print("in delete game: ", request.POST)
    is_active_game = UserGameRecords.objects.filter(game_id=game).update(status='Q')
    success_message = "This game is deleted..."
    print ("User %s deleted game in delete_game() function" % request.user.email)
    return HttpResponseRedirect(reverse('game_results', args=[game]))

def Notification(request):
    if request.is_ajax():

        game_id = request.POST['gameid']
        push_turn_2(game_id)
        
        #game_data=Game.objects.get(game_id=game_id)
        get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
        if get_user_turn.no_of_turns_completed == 1 and get_user_turn.status == 'I':
        #      notification = Notify.objects.get(game_id=game_id)
            mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
            mybid = serializers.serialize('json', mybid)
        #     game_data = serializers.serialize('json', game_data)
        #     data = {'success_message': notification.msg, 'game_id': game_id, 'mybid': mybid, 'game_data': game_data}
            data = {'game_id': game_id, 'mybid':mybid, 'turn': get_user_turn.no_of_turns_completed}
            return HttpResponse(json.dumps(data), content_type='application/json')

def divturn_update(request):
    if request.is_ajax():
        print ("function divturn_update() called by %s from Ajax Request in Play Game Page" %request.user.email)
        game_id = request.GET['gameid']
        game_data = Game.objects.get(id=game_id)
        try:
            get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
            # print ("got record")
            if get_user_turn.status == 'Q':
                print("Identified by %s - Game has been deleted in divturn_update()" %request.user.email)
                data = {'error_message':'This Game has been already started by game owner.', 'game_id':game_id}
                return HttpResponse(json.dumps(data),content_type='application/json')
        except UserGameRecords.DoesNotExist as ex:
            print(ex)

        if get_user_turn.no_of_turns_completed == game_data.no_of_turns_per_player:
            message = "This game is over you cannot bid anymore."
            # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
            # mybid = serializers.serialize('json', mybid)
            #get the number of players == number of players bid

            data = {'error_message': message, 'game_id': game_id,'turn':get_user_turn.no_of_turns_completed, 'game_data': game_data}
            #data = serializers.serialize('json', data)
            return HttpResponse(json.dumps(data),content_type='application/json')

        elif get_user_turn.no_of_turns_completed == 1 and get_user_turn.status == 'I':
            player_bidded= BidValues.objects.filter(game_id=game_id,player_id=request.user.id ,no_of_turn=1 )
            message = "Please wait for the second turn to start."
            # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
            # mybid = serializers.serialize('json', mybid)
            data = {'success': message,'turn':get_user_turn.no_of_turns_completed,'game_id': game_id, 'game_data': game_data}
            data = serializers.serialize('json', data)
            print("turn = 1")
            return HttpResponse(json.dumps(data), content_type='application/json')

        else:
            print(get_user_turn.no_of_turns_completed, ' turns')
            print(get_user_turn.status, ' status')

            if get_user_turn.no_of_turns_completed == 0 and get_user_turn.status == 'B':

                a2b = int(request.GET['a2b'])
                b2a = int(request.GET['b2a'])
                bid_value_obj = BidValues()
                bid_value_obj.game_id = game_data.id
                bid_value_obj.player_id = request.user.id
                bid_value_obj.value_a2b = a2b
                bid_value_obj.value_b2a = b2a
                bid_value_obj.no_of_turn = get_user_turn.no_of_turns_completed + 1
                update_user = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)

                if not BidValues.objects.filter(game_id=game_data.id,no_of_turn=bid_value_obj.no_of_turn,
                        player_id=request.user.id).count():

                    if game_data.no_of_ai_player > 0:
                        udpate_ai_players_bid(game_id, update_user.no_of_turns_completed + 1)

                    bid_value_obj.save()

                update_user.status = 'I'
                update_user.no_of_turns_completed += 1
                update_user.save()
                #get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                get_user_turn = update_user
                message = "Your bid has been placed successfully. Result will be calculated once you move the game to turn 2."
                # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                # mybid = serializers.serialize('json', mybid)
                data = {'success': message, 'turn':get_user_turn.no_of_turns_completed}
                #data=serializers.serialize('json',data)
                print("turn = 0")
                return HttpResponse(json.dumps(data), content_type='application/json')

            elif get_user_turn.no_of_turns_completed >= 1 and get_user_turn.status == 'T':
                a2b = int(request.GET['a2b'])
                b2a = int(request.GET['b2a'])
                bid_value_obj = BidValues()
                bid_value_obj.game_id = game_data.id
                bid_value_obj.player_id = request.user.id
                bid_value_obj.value_a2b = a2b
                bid_value_obj.value_b2a = b2a
                bid_value_obj.no_of_turn = get_user_turn.no_of_turns_completed + 1
                if not BidValues.objects.filter(game_id=game_data.id,no_of_turn=bid_value_obj.no_of_turn,
                    player_id=request.user.id).count():
                    bid_value_obj.save()

                update_user = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                update_user.no_of_turns_completed += 1
                update_user.save()
                get_completed_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)

                if get_completed_turn.no_of_turns_completed == game_data.no_of_turns_per_player:
                    UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                    get_completed_turn.status = 'Q'
                    get_completed_turn.save()
                    get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                    success_message = "Your bid has been placed successfully."
                    error_message = "This game is over; you cannot bid anymore."
                    # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                    # mybid = serializers.serialize('json', mybid)
                    data = {'success': success_message, 'turn':get_user_turn.no_of_turns_completed,'error_message':error_message, 'game_id': game_id, 'game_data': game_data}
                    #data = serializers.serialize('json', data)
                    print("turn >= 1 if")
                    return HttpResponseRedirect('/MyDashboard/')

                else:
                    # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                    get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                    # mybid = serializers.serialize('json', mybid)
                    success_message = "Your bid has been placed successfully."
                    data = {'turn': get_user_turn.no_of_turns_completed,'game_id': game_id,  'success':success_message}
                    #data = serializers.serialize('json', data)
                    print("turn >= 1 else")
                    return HttpResponse(json.dumps(data), content_type='application/json')
        return HttpResponse(json.dumps({'game_id': game_id}), content_type='application/json')

def placeit_divturn_update(request):
    if request.is_ajax():
        print("User %s clicked on Place Bid after First Turn" %request.user.email)
        game_id = request.GET['gameid']
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        turn_id = int(request.GET['turn'])
        
        try:
            get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
            print ("got record")
            if get_user_turn.status == 'Q':
                print("Game has been deleted.")
                data = {'error_message':'This Game has been deleted by the game owner.', 'game_id':game_id}
                return HttpResponse(JsonResponse(data),content_type='application/json')
        except UserGameRecords.DoesNotExist as ex:
            print(ex)

        if get_user_turn.no_of_turns_completed == game_data.no_of_turns_per_player:
            message = "This game is over you cannot bid anymore."
            #mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
            #mybid = serializers.serialize('json', mybid)
            #get the number of players == number of players bid

            data = {'error_message': message, 'game_id': game_id,'turn':get_user_turn.no_of_turns_completed,  'game_data': game_data}
            #data = serializers.serialize('json', data)
            return HttpResponse(JsonResponse(data),content_type='application/json')

        elif get_user_turn.no_of_turns_completed == 1 and get_user_turn.status == 'I':
            player_bidded= BidValues.objects.filter(game_id=game_id,player_id=request.user.id ,no_of_turn=1 )
            message = "Please wait for the second turn to start."
            # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
            # mybid = serializers.serialize('json', mybid)
            data = {'success': message,'turn':get_user_turn.no_of_turns_completed,'game_id': game_id, 'game_data': game_data}
            data = serializers.serialize('json', data)
            print("turn = 1")
            return HttpResponse(JsonResponse(data), content_type='application/json')

        else:

            if get_user_turn.no_of_turns_completed == 0 and get_user_turn.status == 'B':
                a2b = int(request.GET['a2b'])
                b2a = int(request.GET['b2a'])
                update_user = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                bid_value_obj = BidValues()
                bid_value_obj.game_id = game_data.id
                bid_value_obj.player_id = request.user.id
                bid_value_obj.value_a2b = a2b
                bid_value_obj.value_b2a = b2a
                bid_value_obj.no_of_turn = get_user_turn.no_of_turns_completed + 1
                if not BidValues.objects.filter(game_id=game_id,no_of_turn=bid_value_obj.no_of_turn,
                                                player_id=request.user.id).count():

                    # Saving AI Players bid first.
                    if game_data.number_of_players > 0:
                        udpate_ai_players_bid(game_id, update_user.no_of_turns_completed + 1)

                    bid_value_obj.save()
                    update_user.status = 'I'
                    update_user.no_of_turns_completed += 1
                    update_user.save()


                #get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                get_user_turn = update_user
                message = "Your bid has been placed successfully. Result will be calculated once you move the game to turn 2."
                # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                # mybid = serializers.serialize('json', mybid)
                data = {'success': message, 'turn':get_user_turn.no_of_turns_completed}
                #data=serializers.serialize('json',data)
                print("turn = 0")
                return HttpResponse(JsonResponse(data), content_type='application/json')

            elif get_user_turn.no_of_turns_completed >= 1 and get_user_turn.status == 'T':
                a2b = int(request.GET['a2b'])
                b2a = int(request.GET['b2a'])
                update_user = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                bid_value_obj = BidValues()
                bid_value_obj.game_id = game_data.id
                bid_value_obj.player_id = request.user.id
                bid_value_obj.value_a2b = a2b
                bid_value_obj.value_b2a = b2a
                bid_value_obj.no_of_turn = get_user_turn.no_of_turns_completed + 1
                if not BidValues.objects.filter(game_id=game_data.id,no_of_turn=bid_value_obj.no_of_turn,
                    player_id=request.user.id).count():

                    logger.info("Turn No. %d Number of Players %d " %(get_user_turn.no_of_turns_completed, game_data.number_of_players))
                    # Saving AI Players bid first.
                    if game_data.number_of_players > 0:
                        logger.info("Updating AI Players")
                        udpate_ai_players_bid(game_id, update_user.no_of_turns_completed + 1)

                    bid_value_obj.save()
                    
                    update_user.no_of_turns_completed += 1
                    update_user.save()

                #get_completed_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                get_completed_turn = update_user
                if get_completed_turn.no_of_turns_completed - 1 == game_data.no_of_turns_per_player:
                    #UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                    get_completed_turn.status = 'Q'
                    get_completed_turn.save()
                    #get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                    get_user_turn = get_completed_turn
                    success_message = "Your bid has been placed successfully."
                    error_message = "This game is over; you cannot bid anymore."
                    # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                    # mybid = serializers.serialize('json', mybid)
                    data = {'success': success_message, 'turn':get_user_turn.no_of_turns_completed,'error_message':error_message, 'game_id': game_id, 'game_data': game_data}
                    #data = serializers.serialize('json', data)
                    print("turn >= 1 if")
                    return HttpResponse(JsonResponse(data), content_type='application/json')

                else:
                    # mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
                    #get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
                    get_user_turn = get_completed_turn
                    # mybid = serializers.serialize('json', mybid)
                    success_message = "Your bid has been placed successfully."
                    data = {'turn': get_user_turn.no_of_turns_completed,'game_id': game_id, 'success':success_message}
                    # data = serializers.serialize('json', data)
                    print("turn >= 1 else")
                    return HttpResponse(JsonResponse(data), content_type='application/json')
        return HttpResponse(JsonResponse({'game_id': game_id}), content_type='application/json')


def start_bidding_game(request, game_id):
    try:
        get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
        print ("got record")
        if get_user_turn.status == 'Q':
            print("Game has been deleted.")
            data = {'error_message':'This Game has been already started by the game owner.', 'game_id':game_id}
            return HttpResponse(JsonResponse(data),content_type='application/json')
    except UserGameRecords.DoesNotExist as ex:
        print(ex)
    push_turn_2(game_id)
    noted = Notify.objects.get(game_id=game_id)
    noted.msg = 'S'
    noted.save()
    bid_player_count = BidValues.objects.filter(game_id=game_id, no_of_turn=1).count()
    data = {'success_message':'Game Started With {0} players.'.format(bid_player_count), 'game_id':game_id}
    return HttpResponse(JsonResponse(data),content_type='application/json')   

def move_turn(request):
    print("function move_turn()")
    print("User completed First Turn and  clicked the Next Turn button in Play Game page")
    if request.is_ajax():
        game_id = request.GET['gameid']
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        
        try:
            get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
            print ("got record")
            if get_user_turn.status == 'Q':
                print("Game has been deleted.")
                data = {'error_message':'This Game has been already started by the game owner', 'game_id':game_id}
                return HttpResponse(JsonResponse(data), content_type='application/json')
        except UserGameRecords.DoesNotExist as ex:
            print(ex)

        if get_user_turn.no_of_turns_completed == 0:
            resp = divturn_update(request)
            if 'error_message' in resp:
                return resp

        
        push_turn_2(game_id)
        noted = Notify.objects.get(game_id=game_id)
        noted.msg = 'S'
        noted.save()
        get_turn_count = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
        my_turn = get_turn_count.no_of_turns_completed

        message = "Switch to turn 2 Successfully."
        mybid = GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id)
        mybid = serializers.serialize('json', mybid)
        data = {'turn': my_turn,'mybid': mybid, 'success': message}

        # game_time_key = "elapsedTime{}".format(game_id)
        # # request.session[game_time_key] = time.time()   
        # cache.set(game_time_key, time.time()) 
        return HttpResponse(JsonResponse(data), content_type='application/json')
    else:
        return render(request, 'play_game.html')



def refresh_page(request):
    
    if request.is_ajax():
        game_id = request.GET['game']
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        print("function refresh_page()")
        try:
            get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
            print ("got record")
            if get_user_turn.status == 'Q':
                print("Game has been deleted.")
                data = {'error_message':'This Game has been already started by the game owner.', 'game_id':game_id}
                return HttpResponse(JsonResponse(data),content_type='application/json')
        except UserGameRecords.DoesNotExist as ex:
            print(ex)

        turn_limit=game_data.no_of_turns_per_player
        my_turn = request.GET['turn']
        my_turn=int(my_turn)
        turn_match_status =False
        placed_bids = BidValues.objects.filter(game_id=game_id, player_id=request.user.id)
        mybid=GameSimulationDetails.objects.filter(game_id=game_id, player_id=request.user.id).order_by('-id')

        print("placed_bids:  %s" % placed_bids )
        print("mybid: %s" % mybid)
        if len(placed_bids)==len(mybid):
            turn_match_status=True

        timediff=0
        if my_turn > 0:

            last_simulation_data=GameSimulationDetails.objects.latest('player_id')
            dtformat = "%Y-%m-%d %H:%M:%S"
            last_update_time = last_simulation_data.simulation_timestamp
            last_update_time_utc_time = (last_update_time.strftime(dtformat))
            last_update_time_dtobj = datetime.datetime.strptime(last_update_time_utc_time, dtformat)

            current_utc_time = datetime.datetime.now()
            utc_time_str = (current_utc_time.strftime(dtformat))
            utc_time_dtobj = datetime.datetime.strptime(utc_time_str, dtformat)
            timediff = utc_time_dtobj - last_update_time_dtobj

        timediff=str(timediff)
        message = "You have refreshed the page !!!!"
        mybid = serializers.serialize('json', mybid)
        # timediff = serializers.serialize('json', timediff)
        # timediff = json.dump(timediff)
        next_turn_button=False
        if int(my_turn) == 1:
            get_notify=Notify.objects.get(game_id=game_id)
            print(get_notify)
            if get_notify.msg == 'S':
                next_turn_button = True

        data = {'turn': my_turn,'turn_limit':turn_limit,'turn_match_status':turn_match_status,
                'next_turn_status':next_turn_button,'mybid': mybid, 'success': message, 'timediff':timediff}

        return HttpResponse(JsonResponse(data), content_type='application/json')


def update_turn_notify(request):
    if request.is_ajax():
        #logger.info("update_turn_notify - %s" %request.path)
        start_time = time.time()
        #print ("------------------------------")
        #print ("function: update_turn_notify() by %s" %request.user.email)
        game_id = request.GET['game']
        game_data = cache.get("GameDetails%s"%game_id) or Game.objects.get(id=game_id)
        turn_limit=game_data.no_of_turns_per_player

        try:
            get_user_turn = UserGameRecords.objects.get(game_id=game_id, user_id=request.user.id)
            total_finished_turns = BidValues.objects.filter(game_id=game_id, player_id=request.user.id).count()
            print ("got record")
            if get_user_turn.status == 'Q':
                if total_finished_turns == turn_limit:
                    print("Game Turn Limit Reached.")
                    data = {'error_message':'Game Turn Limit Reached', 'game_id':game_id}
                    return HttpResponse(JsonResponse(data),content_type='application/json')
                print("Game has been deleted.")
                data = {'error_message':'', 'game_id':game_id}
                #logger.info("update_turn_notify completed execution in %5.4f seconds" % (time.time() - start_time))
                return HttpResponse(JsonResponse(data), content_type='application/json')
        except UserGameRecords.DoesNotExist as ex:
            print(ex)

        
        my_turn = request.GET['turn']
        my_turn=int(my_turn)
        
        game_turn_list = str(game_id) +"|"+ str(my_turn)
        if my_turn != 1:
            print("Calculating formulas")
            calculate_formulas(game_id, my_turn)
          
        mybid = GameSimulationDetails.objects.filter(game_id=game_id,player_id=request.user.id,no_of_turn=my_turn)
        # remove any extra simulationobjects
        if(len(mybid) > 1):
            actual_sim = mybid[0]
            for game_sim in mybid[1:]:
                game_sim.delete()
            mybid = [actual_sim]
        

        print("turn number ", my_turn)
        status=True
        if int(my_turn) == 1:
            #get_notify=Notify.objects.get(game_id=game_id)
            #print(get_notify)
            # if  get_notify.msg=='F':
            if game_data.force_t2==False:
                status = False
                data = {'turn': my_turn, 'turn_limit': turn_limit, 'status': status}
                print(data)
                #logger.info("update_turn_notify completed execution in %5.4f seconds" % (time.time() - start_time))
                return HttpResponse(JsonResponse(data), content_type='application/json')

        if not mybid:
            status=False
            data = {'turn': my_turn, 'turn_limit':turn_limit,'status': status}
            #logger.info("update_turn_notify completed execution in %5.4f seconds" % (time.time() - start_time))
            return HttpResponse(JsonResponse(data), content_type='application/json')
        # else :
        #     status=True
        # if status:
        #     game_time_key = "elapsedTime{}".format(game_data.id)
        #     # cache.set(game_time_key, time.time())
        #     request.session[game_time_key] = time.time()
        if status:
            get_game_timer(request, game_data.id, my_turn+1, forceUpdate=bool(my_turn!=1))


        mybid = serializers.serialize('json', mybid)
        # mybid = JsonResponse(mybid)
        message = "We have placed the bid and generated the output for turn"
        data = {'turn': my_turn,'turn_limit':turn_limit,'status':status, 'mybid': mybid, 'success': message}
        #logger.info("update_turn_notify completed execution in %5.4f seconds" %(time.time() - start_time))
        return HttpResponse(JsonResponse(data), content_type='application/json')


def download_results(request):
    # http://localhost:8000/download_results/
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="game_results.csv"'

    writer = csv.writer(response)
    writer.writerow(['Game ID', 'Game Name', 'Has AI Players', 'Number of Turns', 'Number of Trucks', "Brokerage Fee",
                     'Cost per Truck', 'Loaded Cost per Truck', 'Shrink Ratio', 'Growth Ratio', 'Unused cost per truck',
                     'Player ID', 'Nick Name', 'A2B', 'B2A', 'A2B Awarded', 'B2A Awarded', 'Net Contribution', 'Contribution per Load'])

    cursor = connection.cursor()
    sql_statement = ("select g.id, g.name, IF(g.is_ai, 'YES', 'NO'), g.no_of_turns_per_player, g.no_of_trucks, g.brokerage_fee, "
                   "g.empty_cost_per_truck, g.loaded_cost_per_truck, g.shrink_ratio, g.growth_ratio, "
                   "g.unused_capital_cost_perTruck, ug.user_id, ug.user_nick_name, gd.value_a2b, gd.value_b2a, "
                   "gd.trucks_a2b_Awarded, gd.trucks_b2a_Awarded, gd.net_contribution, gd.contribution_per_load "
                   "from pricingsimulation_gamesimulationdetails gd inner join pricingsimulation_game g "
                   "on(gd.game_id = g.id) inner join pricingsimulation_usergamerecords ug on "
                   "(gd.player_id = ug.user_id and g.id = ug.game_id) order by g.id, ug.user_id")

    cursor.execute(sql_statement)
    rows = cursor.fetchall()
    for r in rows:
        writer.writerow(list(r))

    return response

def game_status(request, game_id):
    game_id = int(game_id)
    nick_name_dict = {}
    mybid_list = []
    recent_turn_no = 0
    ugr = UserGameRecords.objects.filter(game_id=game_id)

    for u in ugr:
        nick_name_dict[u.user_id] = u.user_nick_name

    player_dict = {}
    mybid = GameSimulationDetails.objects.filter(game_id=game_id).order_by("-id")
    if mybid:
        recent_turn_no = mybid[0].no_of_turn

    players = []
    series = []

    for b in mybid:
        if recent_turn_no != b.no_of_turn: break
        if b.player_id not in player_dict:
            b.cumulative = b.net_contribution
            player_dict[b.player_id] = b.net_contribution
        else:
            player_dict[b.player_id] = player_dict[b.player_id] + b.net_contribution
            b.cumulative = player_dict[b.player_id]

        b.nick_name = nick_name_dict[b.player_id]
        players.append(b.nick_name)
        series.append({'name': 'Player-1', 'data': [b.net_contribution]})
        mybid_list.append(b)

    return render(request, 'game_status.html', {'mybid':mybid_list, 'players':json.dumps(players),
                                                'series':json.dumps(series)})