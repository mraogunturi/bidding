# from __future__ import absolute_import
# import random
# import time
# from celery import shared_task
# from celery.task import task
# from django.db.models import Max
# import math
# from .models import *
# import logging
# import logging.handlers
# import os
# from django.core.cache import cache

# # os.environ['DJANGO_SETTINGS_MODULE'] = 'pricing.settings'
# # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pricing.settings')
# # from django.conf import settings

# LOG_FILENAME = 'logfile.out'

# # Set up a specific logger with our desired output level
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# # Add the log message handler to the logger
# handler = logging.handlers.RotatingFileHandler(
#               LOG_FILENAME, maxBytes=(1048576*5), backupCount=5)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# #logger.debug("starting the celery !!!!! $$$$$$")

# @task
# def force_start(game_id):
#     enable_game = Game.objects.get(id=game_id)
#     no_of_turns_of_game = enable_game.no_of_turns_per_player

#     if enable_game.is_ai and enable_game.no_of_ai_player>0:
#         all_players = []
#         ai_players = []
#         get_ai_players = UserGameRecords.objects.filter(game_id=enable_game.id, status='J')

#         for player in get_ai_players:
#             fleet_size = FleetNetContribution()
#             fleet_size.game_id = enable_game.id
#             fleet_size.trucks_max_awarded = enable_game.no_of_trucks
#             fleet_size.player_id = player.user_id
#             fleet_size.no_of_turn = 1
#             fleet_size.save()
#             all_players.append(player.user_id)
#         get_fleet_info=FleetNetContribution.objects.filter(game_id=game_id,no_of_turn=1)
#         enable_game.number_of_players=get_fleet_info.count()
#         for ai in all_players:
#             #logger.debug(ai,"IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
#             #logger.debug(ai,"IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
#             get_ai = UserProfile.objects.get(user_id=ai)
#             if get_ai.is_ai_player:
#                 ai_players.append(get_ai.user_id)
#         #logger.debug (ai_players,"*******hello******")
#         for turn in range(1, no_of_turns_of_game + 1):
#             for user in ai_players:
#                 update_user_game = UserGameRecords.objects.get(game_id=enable_game.id, user_id=user)
#                 get_current_turn = update_user_game.no_of_turns_completed + 1
#                 a2b = int(random.randint(enable_game.loaded_cost_per_truck, 999))
#                 b2a = int(random.randint(enable_game.loaded_cost_per_truck, 999))
#                 bid_value_obj = BidValues()
#                 bid_value_obj.game_id = enable_game.id
#                 bid_value_obj.player_id = user
#                 bid_value_obj.value_a2b = a2b
#                 bid_value_obj.value_b2a = b2a
#                 bid_value_obj.no_of_turn = get_current_turn
#                 bid_value_obj.save()
#                 update_user_game.no_of_turns_completed += 1
#                 update_user_game.save()

#         for ai in ai_players:
#             update_user_game = UserGameRecords.objects.get(game_id=enable_game.id, user_id=ai)
#             update_user_game.status = 'Q'
#             update_user_game.save()

#     else:
#         #logger.debug("else of Force Start executed")
#         get_all_players=UserGameRecords.objects.filter(game_id=enable_game.id, status='J')
#         all_players = []
#         for player in get_all_players:
#             fleet_size = FleetNetContribution()
#             fleet_size.game_id = enable_game.id
#             fleet_size.trucks_max_awarded = enable_game.no_of_trucks
#             fleet_size.player_id = player.user_id
#             fleet_size.no_of_turn = 1
#             fleet_size.save()
#             all_players.append(player.user_id)
#         get_fleet_info = FleetNetContribution.objects.filter(game_id=game_id, no_of_turn=1)
#         enable_game.number_of_players = get_fleet_info.count()
#         enable_game.total_trucks_AvailableA2B=0.95*enable_game.number_of_players*enable_game.no_of_trucks
#         enable_game.total_trucks_AvailableB2A = 0.75 * enable_game.number_of_players * enable_game.no_of_trucks
#         enable_game.save()
#         #logger.debug("Fleet alterations are being made")
#     return True
# @task
# def start_game():
#     dtformat = "%Y-%m-%d %H:%M:%S"
#     current_utc_time = datetime.datetime.now()
#     utc_time_str = (current_utc_time.strftime(dtformat))
#     utc_time_dtobj = datetime.datetime.strptime(utc_time_str, dtformat)
#     get_games = Game.objects.filter(game_status='P')

#     for game_records in get_games:
#         game_datetime = game_records.start_date_time
#         game_datetime_str = (game_datetime.strftime(dtformat))
#         game_datetime_dtobj = datetime.datetime.strptime(game_datetime_str, dtformat)
#         if utc_time_dtobj == game_datetime_dtobj:
#             enable_game = Game.objects.get(id=game_records.id)
#             enable_game.game_status = 'S'
#             enable_game.save()
            
#             no_of_turns_of_game = enable_game.no_of_turns_per_player
#             if enable_game.is_ai:
#                 all_players = []
#                 ai_players = []
#                 get_ai_players = UserGameRecords.objects.filter(game_id=enable_game.id, status='J')
#                 for player in get_ai_players:
#                     all_players.append(player.user_id)
#                 for ai in all_players:
#                     get_ai = UserProfile.objects.get(user_id=ai)
#                     if get_ai.is_ai_player:
#                         ai_players.append(get_ai.user_id)
#                 for turn in range(1, no_of_turns_of_game + 1):
#                    for user in ai_players:
#                        update_user_game = UserGameRecords.objects.get(game_id=enable_game.id, user_id=user)
#                         get_current_turn = update_user_game.no_of_turns_completed + 1
#                         a2b = int(random.randint(enable_game.loaded_cost_per_truck, 999))
#                         b2a = int(random.randint(enable_game.loaded_cost_per_truck, 999))
#                         bid_value_obj = BidValues()
#                         bid_value_obj.game_id = enable_game.id
#                         bid_value_obj.player_id = user
#                         bid_value_obj.value_a2b = a2b
#                         bid_value_obj.value_b2a = b2a
#                         bid_value_obj.no_of_turn = get_current_turn
#                         bid_value_obj.save()
#                         update_user_game.no_of_turns_completed += 1
#                         update_user_game.save()

#                 for ai in ai_players:
#                     update_user_game = UserGameRecords.objects.get(game_id=enable_game.id, user_id=ai)
#                     # if enable_game.no_of_turns_per_player==update_user_game.no_of_turns_completed:
#                     update_user_game.status = 'Q'
#                     update_user_game.save()
#             else:
#                 time.sleep(60)  # 60 is seconds
#             # celery.current_app.send_task('pricingsimulation.tasks.calculate_formulas', args=[enable_game.id])
#             return True

# @task
# def calculate_formulas(gameid, turn_change_required=False):
#     gameid = gameid.split('|')
#     game_id=int(gameid[0])
#     turn=int(gameid[1])
#     get_game_data = Game.objects.get(id=game_id)
#     get_total_turns = int(gameid[1])
#     #logger.debug("line 124 "+str(get_total_turns))
#     get_player_limit = get_game_data.number_of_players
#     #logger.debug("line 126 "+ str(get_player_limit))
    
#     flag = True
#     game_time_key = "elapsedTime{}".format(get_game_data.id)

#     while flag==True:
#         temp_count = turn

#         if temp_count > get_total_turns:
#             #logger.debug("****************temp_count " + str(temp_count))
#             #logger.debug("****************temp_count " + str(temp_count))
#             flag=False
#             #logger.debug("Turn Over Exit Line 144")
#             #logger.debug("Turn Over Exit Line 144")
#             break
#         else:
#             same_turn_paritcipants = BidValues.objects.filter(game_id=game_id, no_of_turn=temp_count)
#             #logger.debug(same_turn_paritcipants)
#             #logger.debug(same_turn_paritcipants)
#             #logger.debug("**** same_turn_participants *****" + str(same_turn_paritcipants.count()))
#             #logger.debug("**** get_player_limit *****" + str(get_player_limit))
#             #logger.debug("**** temp_count ********"+str(temp_count))
#             if same_turn_paritcipants.count() == get_player_limit:
                
#                 update_simulation(game_id,turn,get_player_limit)
#                 players=[]

#                 game = Game.objects.get(id=gameid[0])
#                 obj = TurnAlert()  # object creation
#                 obj.game_id = game.id
#                 obj.turn_no = temp_count
#                 obj.status = 'S'
#                 obj.save()
#                 flag = False
#                 last_turn_update = datetime.datetime.now()
#                 # cache key has been deleted
#                 # cache.delete(game_time_key) # delete game key
#                 cache.set(game_time_key, time.time())
#                 # print("{} time has been set %s".format(game_time_key, time.time()))
#                 break

#             else:

#                 #logger.debug("Else Structure of the simulation condition")
#                 flag = False
                
#                 # elapsed_time = settings.INTERNAL_CACHE.get(game_time_key)
#                 elapsed_time = cache.get(game_time_key)
#                 # print(cache, "cache_object")
#                 if elapsed_time is None:
#                     # settings.INTERNAL_CACHE.set(game_time_key, time.time())
#                     cache.set(game_time_key, time.time())
#                     # print("{} time has been set".format(game_time_key))
#                     continue
#                 # print("elapsed_time ********************************************")
#                 # print("elapsed time: %s" % (time.time() - elapsed_time))
#                 if (time.time() - elapsed_time) > 65:
#                     #logger.debug("player turn bidding updated automatically")
#                     update_Player_not_bidded(game_id, turn, get_game_data.no_of_turns_per_player)
#                     # settings.INTERNAL_CACHE.set(game_time_key, time.time())
#                     cache.set(game_time_key, time.time())
#                 # last_turn_update = same_turn_paritcipants.aggregate(Max('time_stamp'))
#                 # last_tunr_update_secs = (datetime.datetime.now() - last_turn_update['time_stamp__max']).total_seconds()
#                 # # # player_turns_remaining = get_player_limit-same_turn_paritcipants.count()
#                 # # # player_turns_remaining = player_turns_remaining if player_turns_remaining > 0 else 0
                
#                 # # #logger.debug(" elapsed time : " + str(last_tunr_update_secs))
#                 # # # #logger.debug(" palyer time: " + str(player_turns_remaining * 65))
#                 # if (last_tunr_update_secs > 62) and (temp_count > 1): # (player_turns_remaining * 65):
#                 #     #logger.debug("player turn bidding updated automatically")
#                 #     update_Player_not_bidded(game_id, turn, get_game_data.no_of_turns_per_player)
#                 #     last_turn_update = datetime.datetime.now()


# # noinspection PyPep8,PyPep8Naming
# def update_simulation(gameid, turn, total_no_players):
    
#     #logger.debug("TURN NUMBER: "+str(turn))
#     a2b_award_trucks = award_A2B(gameid,turn, total_no_players)
#     b2a_award_trucks = award_B2A(gameid,turn, total_no_players)
#     #logger.debug("b2a_award_trucks %s" % b2a_award_trucks)
#     #logger.debug("a2b_award_trucks %s " % a2b_award_trucks)
#     game_data = Game.objects.get(id=gameid)
#     turn=turn
#     fields = GameSimulationDetails._meta
#     for (user, a2bvalue), (player, b2avalue) in zip(sorted(a2b_award_trucks.items()), sorted(b2a_award_trucks.items())):
#         user_id = User.objects.get(id=user)
#         get_bid_values = BidValues.objects.get(game_id=gameid, no_of_turn=turn, player_id=user_id.id)
#         #logger.debug( "*****************8**%s" % get_bid_values.player_id)
#         # noinspection PyPep8Naming
#         trucks_a2b_Awarded =  a2bvalue
#         #logger.debug("trucks_a2b_Awarded  %s", trucks_a2b_Awarded)
#         # noinspection PyPep8Naming
#         trucks_b2a_Awarded =  b2avalue
#         #logger.debug("trucks_b2a_Awarded %s", trucks_b2a_Awarded)
#         trucks_max_awarded = max(trucks_a2b_Awarded, trucks_b2a_Awarded)
#         revenue = (get_bid_values.value_a2b * trucks_a2b_Awarded) + (get_bid_values.value_b2a * trucks_b2a_Awarded)
#         loaded_cost = trucks_max_awarded * game_data.loaded_cost_per_truck
#         empty_cost = (2 * trucks_a2b_Awarded - trucks_b2a_Awarded) * game_data.empty_cost_per_truck
#         # noinspection PyPep8Naming
#         UnusedCost = (game_data.no_of_trucks - trucks_a2b_Awarded) * game_data.unused_capital_cost_perTruck
        
#         fleet_size = calculate_fleet_size(turn, user_id.id, game_data)
#         fleet_size = fleet_size

#         # noinspection PyPep8
#         if get_bid_values.value_a2b > game_data.brokerage_fee and get_bid_values.value_b2a > game_data.brokerage_fee:
            
#             trucks_max_awarded=0
#             net_contribution = 0
#             contribution_per_load = 0
#         elif get_bid_values.value_a2b < 0 and get_bid_values.value_b2a < 0:
#             net_contribution = -1
#         elif get_bid_values.value_a2b < game_data.loaded_cost_per_truck and get_bid_values.value_b2a < game_data.empty_cost_per_truck:
#             net_contribution = revenue - loaded_cost - empty_cost - UnusedCost - 100
#         else:
#              net_contribution=revenue-((game_data.loaded_cost_per_truck*2)* trucks_max_awarded)-((fleet_size - trucks_max_awarded)*game_data.unused_capital_cost_perTruck)
#         # net_contribution -= ((game_data.no_of_trucks - trucks_max_awarded)*game_data.unused_capital_cost_perTruck)
#         if get_bid_values.value_a2b > game_data.brokerage_fee and get_bid_values.value_b2a > game_data.brokerage_fee:
#             trucks_max_awarded=0
#             contribution_per_load=0
#             loaded_ratio = 0
#         else:
#             try:
#                 contribution_per_load = net_contribution / (trucks_a2b_Awarded + trucks_b2a_Awarded)
#                 loaded_ratio=(trucks_a2b_Awarded + trucks_b2a_Awarded)/(2*trucks_max_awarded)
#             except ZeroDivisionError as ex:
#                 #logger.debug(ex)
#                 contribution_per_load = 0
#                 loaded_ratio = 0

#         game_prev_data=GameSimulationDetails.objects.filter(game_id=game_data.id, no_of_turn=turn,player_id=user_id.id)
#         if game_prev_data.count()==0 :
#             #logger.debug("saving trucks_a2b_Awarded %s", trucks_a2b_Awarded)
#             #logger.debug("saving trucks_b2a_Awarded %s", trucks_b2a_Awarded)

#             data = GameSimulationDetails(game_id=game_data.id,
#                                          player_id=user_id.id,
#                                          value_a2b=get_bid_values.value_a2b,
#                                          value_b2a=get_bid_values.value_b2a,
#                                          trucks_a2b_Awarded=trucks_a2b_Awarded,
#                                          trucks_b2a_Awarded=trucks_b2a_Awarded,
#                                          trucks_max_awarded=trucks_max_awarded,
#                                          no_of_turn=turn,
#                                          revenue=revenue,
#                                          loaded_cost=loaded_cost,
#                                          empty_cost=empty_cost,
#                                          net_contribution=net_contribution,
#                                          contribution_per_load=contribution_per_load,
#                                          loaded_ratio=loaded_ratio,
#                                          fleet_size=fleet_size)
#             data.save()

#             current_fleet=FleetNetContribution.objects.filter(game_id=game_data.id, player_id=data.player_id,no_of_turn=turn)

#             if current_fleet.count()==0:
#                 if data.no_of_turn > 1  :
#                     old_fleet = FleetNetContribution.objects.get(game_id=game_data.id, player_id=data.player_id,
#                                                                  no_of_turn=turn - 1)
#                     #logger.debug("Old Fleet data")

#                     if data.net_contribution > 0 and data.no_of_turn==turn :

#                         new_fleet=FleetNetContribution()
#                         new_fleet.game_id=gameid
#                         new_fleet.player_id=user_id.id
#                         new_fleet.no_of_turn=data.no_of_turn
#                         new_fleet.trucks_max_awarded=old_fleet.trucks_max_awarded * game_data.growth_ratio
#                         new_fleet.net_contribution=data.net_contribution
#                         new_fleet.save()
#                     elif data.net_contribution ==0 and data.no_of_turn==turn :

#                         new_fleet=FleetNetContribution()
#                         new_fleet.game_id=gameid
#                         new_fleet.player_id=user_id.id
#                         new_fleet.no_of_turn=data.no_of_turn
#                         new_fleet.trucks_max_awarded=old_fleet.trucks_max_awarded * game_data.shrink_ratio
#                         new_fleet.net_contribution=data.net_contribution
#                         new_fleet.save()
#                     else :
#                         new_fleet = FleetNetContribution()
#                         new_fleet.game_id = gameid
#                         new_fleet.player_id = user_id.id
#                         new_fleet.no_of_turn = data.no_of_turn
#                         new_fleet.trucks_max_awarded = old_fleet.trucks_max_awarded * game_data.shrink_ratio
#                         new_fleet.net_contribution = data.net_contribution
#                         new_fleet.save()
#                 elif data.no_of_turn==1:
#                     new_fleet = FleetNetContribution()
#                     new_fleet.game_id = gameid
#                     new_fleet.player_id = user_id.id
#                     new_fleet.no_of_turn = data.no_of_turn
#                     # new_fleet=FleetNetContribution.objects.get(game_id=game_data.id, player_id=user_id.id,no_of_turn=1)
#                     new_fleet.net_contribution=data.net_contribution
#                     if data.net_contribution > 0 and data.no_of_turn==turn :
#                         new_fleet.trucks_max_awarded = new_fleet.trucks_max_awarded * game_data.growth_ratio
#                         new_fleet.save()
#                     elif data.net_contribution == 0 and data.no_of_turn == turn:
#                         new_fleet.trucks_max_awarded = new_fleet.trucks_max_awarded
#                         new_fleet.save()
#                     else:
#                         new_fleet.trucks_max_awarded = new_fleet.trucks_max_awarded * game_data.shrink_ratio
#                         new_fleet.save()
#                 else:
#                     #logger.debug("Calculation for fleet not needed ")
#                     pass
#             else:
#                 #logger.debug("Fleet tried adding twice")
#                 pass
#     return True

# #Diff logic
# def award_a2b(gameid, turn):
#     game_table = Game.objects.get(id=gameid)
#     if turn > 1:
#         get_previous_values=BidValues.objects.filter(game_id=gameid,no_of_turn=turn-1)

#         get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#         #logger.debug("^^^^^^^^^^^^^^^^^^^" +  get_bid_values + "^^^^^^^^^^^^^^^^^")
#         #logger.debug("^^^^^^^************"+ get_previous_values + "*******^^^^^")

#         if get_previous_values.count() > get_bid_values.count():
#             players_last_turn=[]
#             players_not_bidded=[]
#             for prev_bid in get_previous_values:
#                 players_last_turn.append(prev_bid.player_id)

#             for curr_bid in get_bid_values:
#                 each_player=curr_bid.player_id
#                 if players_last_turn.count(each_player)==0:
#                     players_not_bidded.append(each_player)

#             #logger.debug("*******players not bidded****" + players_not_bidded)
#             for nb in players_not_bidded:
#                 get_prev=BidValues.objects.get(game_id=gameid,no_of_turn=turn-1,player_id=nb)
#                 fake_bid=BidValues()
#                 fake_bid.value_a2b=get_prev.value_a2b
#                 fake_bid.save()
#     get_new_bids=BidValues.objects.filter(game_id=gameid, no_of_turn=turn)

#     a2b = {}
#     for i in get_new_bids:
#         a2b[i.player_id] = i.value_a2b

#     available_trucksA2B = i * 0.95 * game_table.no_of_trucks * game_table.number_of_players

#     suma2b = sum(a2b.values())
#     seq = [x for x in a2b]
#     ratio = [a2b[x] / suma2b for x in a2b]
#     ratio.reverse()
#     award = []

#     for i in ratio:
#         award.append(int(
#             i * 0.95 * game_table.no_of_trucks * game_table.number_of_players))  # 95% of num_of_trucks* num_of_playres
#     data = {k: v for k, v in zip(seq, award)}
#     return data

# #Diff logic
# def award_b2a(gameid, turn):
#     game_table = Game.objects.get(id=gameid)
#     # get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#     if turn>1:
#         get_previous_values=BidValues.objects.filter(game_id=gameid,no_of_turn=turn-1)

#         get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#         #logger.debug("^^^^^^^^^^^^^^^^^^^"+ get_bid_values + "^^^^^^^^^^^^^^^^^")
#         #logger.debug("^^^^^^^************"+ get_previous_values + "*******^^^^^")

#         if len(get_previous_values)> len(get_bid_values):
#             players_last_turn=[]
#             players_not_bidded=[]
#             for prev_bid in get_previous_values:
#                 players_last_turn.append(prev_bid.player_id)

#             for curr_bid in get_bid_values:
#                 each_player=curr_bid.player_id
#                 if players_last_turn.count(each_player)==0:
#                     players_not_bidded.append(each_player)

#             #logger.debug("*******players not bidded****"+ players_not_bidded)
#             for nb in players_not_bidded:
#                 get_prev=BidValues.objects.get(game_id=gameid,no_of_turn=turn-1,player_id=nb)
#                 fake_bid=BidValues()
#                 fake_bid.value_b2a=get_prev.value_b2a
#                 fake_bid.save()
#     get_new_bids=BidValues.objects.filter(game_id=gameid, no_of_turn=turn)

#     b2a = {}
#     for i in get_new_bids:
#         b2a[i.player_id] = i.value_b2a
#     sumb2a = sum(b2a.values())
#     seq = [x for x in b2a]
#     ratio = [b2a[x] / sumb2a for x in b2a]
#     ratio.reverse()
#     award = []
#     for i in ratio:
#         award.append(int(
#            0.75* i * game_table.total_trucks_AvailableB2A))  # 75% of num_of_trucks* num_of_playres
#     data = {k: v for k, v in zip(seq, award)}
#     return data

# @task
# def end_game():
#     dtformat = "%Y-%m-%d %H:%M:%S.%f"
#     current_utc_time = datetime.datetime.now()
#     utc_time_str = (current_utc_time.strftime(dtformat))
#     utc_time_dtobj = datetime.datetime.strptime(utc_time_str, dtformat)
#     get_games = Game.objects.filter(game_status='S')

#     for game_records in get_games:
#         game_datetime = game_records.start_date_time
#         game_datetime_str = (game_datetime.strftime(dtformat))
#         game_datetime_dtobj = datetime.datetime.strptime(game_datetime_str, dtformat)
#         if utc_time_dtobj == game_datetime_dtobj:
#             disable_game = Game.objects.get(id=game_records.id)
#             disable_game.game_status = 'E'
#             disable_game.save()
#     return True


# @task
# def push_turn_2(game_id):
#     non_participants = UserGameRecords.objects.filter(game_id=game_id, status='B').update(status='Q') #update(status='Q')
#     #logger.debug("non_participants: %s" , non_participants)
#     participants = UserGameRecords.objects.filter(game_id=game_id, status='I').update(status='T')#5
#     #logger.debug("participants: %s" , participants)
#     get_game_data = Game.objects.get(id=game_id)
#     get_game_data.force_t2 = True
#     get_game_data.force_timestamp=datetime.datetime.now()
#     get_game_data.number_of_players = get_game_data.number_of_players - non_participants
#     get_game_data.total_trucks_AvailableA2B = get_game_data.number_of_players*get_game_data.loaded_cost_per_truck
#     #logger.debug(get_game_data.total_trucks_AvailableA2B)
#     get_game_data.total_trucks_AvailableB2A = get_game_data.number_of_players*get_game_data.empty_cost_per_truck
#     #logger.debug(get_game_data.total_trucks_AvailableB2A)
#     get_game_data.no_of_normal_players = participants
#     number_of_bids = BidValues.objects.filter(game_id=game_id, no_of_turn=1)
#     bidded_turn1=number_of_bids.count()
#     get_game_data.number_of_players=bidded_turn1
#     get_game_data.save()

#     # fleet_new_data=FleetNetContribution()
#     update_simulation(game_id, 1, bidded_turn1)

#     get_game_data.total_trucks_AvailableA2B = 0.95 * get_game_data.number_of_players*get_game_data.no_of_trucks
#     get_game_data.total_trucks_AvailableB2A = 0.75 * get_game_data.number_of_players*get_game_data.no_of_trucks
#     get_game_data.save()
#     game = Game.objects.get(id=game_id)
#     turn_alert_data = TurnAlert()
#     turn_alert_data.game_id = game.id
#     turn_alert_data.turn_no = 1
#     turn_alert_data.status = 'S'
#     turn_alert_data.save()

# @task
# def update_Player_not_bidded(gameid, turn, player_bid_limit):
#     game_table = Game.objects.get(id=gameid)
#     if turn <= 1:
#         return

#     get_previous_values=BidValues.objects.filter(game_id=gameid,no_of_turn=turn-1)

#     get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#     #logger.debug("^^^^^^^^^^^^^^^^^^^ %s ^^^^^^^^^^^^^^^^^" % get_bid_values)
#     #logger.debug("^^^^^^^************ %s *******^^^^^" % get_previous_values)

#     if get_previous_values.count() > get_bid_values.count():
#         #logger.debug("&&&& $$$ ##### @@@@")
#         players_last_turn=[]
#         players_not_bidded=[]
#         players_last_turn = [ prev_bid.player_id for prev_bid in get_previous_values]
#         players_not_bidded = list(set(players_last_turn) - set([curr_bid.player_id for curr_bid in get_bid_values]))
        

#         #logger.debug("*******players not bidded**** %s" % players_not_bidded)
#         for nb in players_not_bidded:
            
#             get_prev=BidValues.objects.get(game_id=gameid,no_of_turn=turn-1,player_id=nb)
#             fake_bid=BidValues()
#             fake_bid.game_id = gameid
#             fake_bid.player_id = nb
#             fake_bid.value_a2b=get_prev.value_a2b
#             fake_bid.value_b2a=get_prev.value_b2a
#             fake_bid.no_of_turn = turn
#             try:
#                 UserGameRecords.objects.get(game_id=gameid, user_id=nb, no_of_turns_completed=turn)
#             except UserGameRecords.DoesNotExist:
                
#                 if not BidValues.objects.filter(game_id=gameid,no_of_turn=turn,player_id=nb).count():
#                     fake_bid.save()
#                 #logger.debug("%s player bid saved." % game_table.user.username)
#                 update_user_game = UserGameRecords.objects.get(game_id=gameid, user_id=nb)
#                 update_user_game.no_of_turns_completed = turn
#                 update_user_game.save()
#                 #logger.debug("%s user turns: %s" % (game_table.user.username, update_user_game.no_of_turns_completed))

#                 old_fleet = FleetNetContribution.objects.get(game_id=gameid, player_id=nb, no_of_turn=turn - 1)
#                 new_fleet=FleetNetContribution()
#                 new_fleet.game_id=gameid
#                 new_fleet.player_id=nb
#                 new_fleet.no_of_turn=turn
#                 new_fleet.trucks_max_awarded=old_fleet.trucks_max_awarded
#                 new_fleet.net_contribution=old_fleet.net_contribution
#                 new_fleet.save()

#             if turn == player_bid_limit:
#                 #logger.debug("##### User is quitting!!!!!!!")
#                 # quit this users at once upon BID truns completion
#                 UserGameRecords.objects.filter(game_id=gameid, user_id=nb).update(status='Q')


# def calculate_awards(data_fleet_awarded, brokerage_fee, available_tucks):
#     total_trucks  = 0
#     processed_players = 0
#     for k in sorted(data_fleet_awarded.keys()):
#         if (total_trucks >= available_tucks):
#             break
        
#         reqards_bids = data_fleet_awarded[k]
#         if len(reqards_bids) == 1: # bid with single player
#             i = reqards_bids[0]
#             if i['a2b'] > brokerage_fee:
#                 i['fleet_size'] = 0
#                 continue
#             fleet_size = i['old_fleet_size']
#             if (total_trucks + fleet_size)  > available_tucks:
#                 fleet_size = available_tucks - total_trucks
#             i['fleet_size'] = fleet_size
#             total_trucks += fleet_size
#             #logger.debug("allocated fleet size: %s" % (i))
#             continue

#         same_bid_player_processed = set()
#         while True:
#             if (len(same_bid_player_processed) == len(reqards_bids)) or (total_trucks >= available_tucks):
#                 #logger.debug("allocated fleet size: %s" % (reqards_bids))
#                 break
#             for i in reqards_bids:
#                 if i['player'] in same_bid_player_processed:
#                     continue
#                 if i['a2b'] > brokerage_fee:
#                     i['fleet_size'] = 0
#                     same_bid_player_processed.update([i['player']])
#                     continue
#                 if (total_trucks >= available_tucks):
#                     break
#                 if i['fleet_size'] >= i['old_fleet_size']:
#                     same_bid_player_processed.update([i['player']])
#                     continue
                
#                 i['fleet_size'] += 1
#                 total_trucks += 1


#     return data_fleet_awarded


# def calculate_fleet_size(turn, player_id, game_table):
#     if turn == 1:
#         return game_table.no_of_trucks
    
#     pre_simulation = GameSimulationDetails.objects.filter(game_id=game_table.id, no_of_turn=turn-1,player_id=player_id)
#     # remove any extra simulationobjects
#     if(len(pre_simulation) > 1):
#         actual_sim = pre_simulation[0]
#         for game_sim in pre_simulation[1:]:
#             game_sim.delete()
#         pre_simulation = actual_sim
#     else:
#         pre_simulation = pre_simulation[0]
    
#     if pre_simulation.net_contribution>0:
#         fleet_size = math.ceil(pre_simulation.fleet_size * game_table.growth_ratio)
#     else:
#         fleet_size = math.floor(pre_simulation.fleet_size * game_table.shrink_ratio)
#     #logger.debug("fleet_size: %s, net_contribution: %s, turn number: %s", fleet_size, pre_simulation.net_contribution, turn)
#     return fleet_size


# def award_A2B(gameid, turn, total_no_players):
#     game_table = Game.objects.get(id=gameid)
#     if turn > 1:
#         get_previous_values=BidValues.objects.filter(game_id=gameid,no_of_turn=turn-1)

#         get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#         #logger.debug("^^^^^^^^^^^^^^^^^^^ %s ^^^^^^^^^^^^^^^^^" % get_bid_values)
#         #logger.debug("^^^^^^^************ %s *******^^^^^" % get_previous_values)

#         if get_previous_values.count() > get_bid_values.count():
#             players_last_turn=[]
#             players_not_bidded=[]
#             players_last_turn = [ prev_bid.player_id for prev_bid in get_previous_values]
#             players_not_bidded = list(set(players_last_turn) - set([curr_bid.player_id for curr_bid in get_bid_values]))
            
#             #logger.debug("*******players not bidded**** %s",  players_not_bidded)
#             for nb in players_not_bidded:
#                 get_prev=BidValues.objects.get(game_id=gameid,no_of_turn=turn-1,player_id=nb)
#                 fake_bid=BidValues()
#                 fake_bid.game_id = gameid
#                 fake_bid.player_id = nb
#                 fake_bid.value_a2b=get_prev.value_a2b
#                 fake_bid.value_b2a=get_prev.value_b2a
#                 fake_bid.no_of_turn = turn
#                 # fake_bid=BidValues()
#                 # fake_bid.value_a2b=get_prev.value_a2b
#                 if not BidValues.objects.filter(game_id=gameid,no_of_turn=turn,player_id=nb).count():
#                     fake_bid.save()
#     get_new_bids=BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#     available_tucks = math.floor(0.90 * game_table.no_of_trucks * total_no_players)
    
#     a2b = {}
    
#     total_rewards = 0
#     data_fleet_awarded = {}
#     for i in get_new_bids:
#         a2b[i.player_id] = i.value_a2b
#         total_rewards += i.value_a2b
#         fleet_size = calculate_fleet_size(turn, i.player_id, game_table)
#         data_fleet_awarded.setdefault(i.value_a2b, []).append({'player':i.player_id, 'a2b':i.value_a2b, 'old_fleet_size':math.floor(fleet_size), 'fleet_size':0})
#     #logger.debug("data_fleet_awarded : %s" % data_fleet_awarded)
#     #logger.debug("avaialbl trucks: %s" % available_tucks)
    

#     data_fleet_awarded = calculate_awards(data_fleet_awarded, game_table.brokerage_fee, available_tucks)
#     data = {i:j['fleet_size'] for i in a2b for k,v in data_fleet_awarded.items() for j in v if i==j['player']}
#     return data

# def award_B2A(gameid, turn, total_no_players):
#     game_table = Game.objects.get(id=gameid)
#     if turn > 1:
#         get_previous_values=BidValues.objects.filter(game_id=gameid,no_of_turn=turn-1)

#         get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#         #logger.debug("^^^^^^^^^^^^^^^^^^^ %s ^^^^^^^^^^^^^^^^^" % get_bid_values)
#         #logger.debug("^^^^^^^************ %s *******^^^^^" % get_previous_values)

#         if get_previous_values.count() > get_bid_values.count():
#             players_last_turn=[]
#             players_not_bidded=[]
#             for prev_bid in get_previous_values:
#                 players_last_turn.append(prev_bid.player_id)

#             for curr_bid in get_bid_values:
#                 each_player=curr_bid.player_id
#                 if players_last_turn.count(each_player)==0:
#                     players_not_bidded.append(each_player)

#             #logger.debug("*******players not bidded****"+ players_not_bidded)
#             for nb in players_not_bidded:
#                 get_prev=BidValues.objects.get(game_id=gameid,no_of_turn=turn-1,player_id=nb)
#                 fake_bid=BidValues()
#                 fake_bid.game_id = gameid
#                 fake_bid.player_id = nb
#                 fake_bid.value_a2b=get_prev.value_a2b
#                 fake_bid.value_b2a=get_prev.value_b2a
#                 fake_bid.no_of_turn = turn
#                 # fake_bid.value_b2a=get_prev.value_b2a
#                 if not BidValues.objects.filter(game_id=gameid,no_of_turn=turn,player_id=nb).count():
#                     fake_bid.save()
    
#     get_new_bids=BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
#     available_tucks = math.floor((0.9 * game_table.no_of_trucks * total_no_players) * 0.8)
    
#     a2b = {}
#     total_rewards = 0
#     data_fleet_awarded = {}
#     for i in get_new_bids:
#         a2b[i.player_id] = i.value_b2a
#         total_rewards += i.value_b2a
#         fleet_size = calculate_fleet_size(turn, i.player_id, game_table)
#         data_fleet_awarded.setdefault(i.value_b2a, []).append({'player':i.player_id, 'a2b':i.value_b2a, 'old_fleet_size':math.floor(fleet_size), 'fleet_size':0})
#     # get_fleet_info=FleetNetContribution.objects.filter(game_id=gameid,no_of_turn=turn-1)
#     # data_fleet_awarded = sorted(, key=lambda x:x['a2b'])
#     #logger.debug("data_fleet_awarded : %s" % data_fleet_awarded)
#     #logger.debug("avaialbl trucks: %s" % available_tucks)
    
#     data_fleet_awarded = calculate_awards(data_fleet_awarded, game_table.brokerage_fee, available_tucks)

#     data = {i:j['fleet_size'] for i in a2b for k,v in data_fleet_awarded.items() for j in v if i==j['player']}
#     return data

