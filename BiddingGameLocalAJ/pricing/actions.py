from pricingsimulation.models import Game, BidValues, GameSimulationDetails, UserGameRecords, TurnAlert
import math
import datetime
import time
from django.core.cache import cache

def get_all_games(user_id):

    played_games = UserGameRecords.objects.filter(status__in=['T', 'Q', 'E']).values('game_id')

    pending_games = Game.objects.filter(is_active=True, start_date_time__gte=datetime.date.today()).exclude(
        game_status='E').exclude(id__in=[i['game_id'] for i in played_games])

    user_active_games = UserGameRecords.objects.filter(user_id=user_id).values('game_id')
    user_games = [g['game_id'] for g in user_active_games]

    return pending_games, user_games


def calculate_awards(data_fleet_awarded, brokerage_fee, available_tucks):
    total_trucks = 0
    processed_players = 0
    for k in sorted(data_fleet_awarded.keys()):
        if (total_trucks >= available_tucks):
            break

        reqards_bids = data_fleet_awarded[k]
        if len(reqards_bids) == 1:  # bid with single player
            i = reqards_bids[0]
            if i['a2b'] > brokerage_fee:
                i['fleet_size'] = 0
                continue
            fleet_size = i['old_fleet_size']
            if (total_trucks + fleet_size) > available_tucks:
                fleet_size = available_tucks - total_trucks
            i['fleet_size'] = fleet_size
            total_trucks += fleet_size
            # logger.debug("allocated fleet size: %s" % (i))
            continue

        same_bid_player_processed = set()
        while True:
            if (len(same_bid_player_processed) == len(reqards_bids)) or (total_trucks >= available_tucks):
                # logger.debug("allocated fleet size: %s" % (reqards_bids))
                break
            for i in reqards_bids:
                if i['player'] in same_bid_player_processed:
                    continue
                if i['a2b'] > brokerage_fee:
                    i['fleet_size'] = 0
                    same_bid_player_processed.update([i['player']])
                    continue

                if (total_trucks >= available_tucks):
                    break

                if i['fleet_size'] >= i['old_fleet_size']:
                    same_bid_player_processed.update([i['player']])
                    continue

                i['fleet_size'] += 1
                total_trucks += 1

    return data_fleet_awarded


def calculate_fleet_size(turn, player_id, game_table, game_simulation_details):
    if turn == 1:
        return game_table.no_of_trucks

    pre_simulation = []
    for gs in game_simulation_details:
        if gs.no_of_turn == turn-1 and gs.player_id == player_id:
            pre_simulation.append(gs)
            break

    #pre_simulation = GameSimulationDetails.objects.filter(game_id=game_table.id, no_of_turn=turn - 1,  player_id=player_id)
    # print(turn, " turn number")
    # print(pre_simulation, " pre_simulation")
    # remove any extra simulationobjects
    if len(pre_simulation) > 1:
        actual_sim = pre_simulation[0]
        for game_sim in pre_simulation[1:]:
            game_sim.delete()
        pre_simulation = actual_sim
    else:
        pre_simulation = pre_simulation[0]

    if pre_simulation.net_contribution > 0:
        fleet_size = math.ceil(pre_simulation.fleet_size * game_table.growth_ratio)
    else:
        fleet_size = math.floor(pre_simulation.fleet_size * game_table.shrink_ratio)
    # logger.debug("fleet_size: %s, net_contribution: %s, turn number: %s", fleet_size, pre_simulation.net_contribution, turn)
    return fleet_size


def award_A2B(game, turn, total_no_players, prev_bidvalues=[], current_bidvalues=[], game_simulation_values=[]):
    '''
    :param game: An object of Game
    :param turn: current turn number
    :param total_no_players: number of players in the game
    :param prev_bidvalues: A list of BidValues object
    :param current_bidvalues: A list of BidValues object
    :param game_simulation_values: A list of Game Simulation objects
    :return:
    '''
    #game_table = cache.get("GameDetails%s" % gameid) or Game.objects.get(id=gameid)
    if turn > 1:
        #get_previous_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn - 1)

        #get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
        # logger.debug("^^^^^^^^^^^^^^^^^^^ %s ^^^^^^^^^^^^^^^^^" % get_bid_values)
        # logger.debug("^^^^^^^************ %s *******^^^^^" % get_previous_values)

        if len(prev_bidvalues) > len(current_bidvalues):
            players_last_turn = []
            players_not_bidded = []
            players_last_turn = [prev_bid.player_id for prev_bid in prev_bidvalues]
            players_not_bidded = list(set(players_last_turn) - set([curr_bid.player_id for curr_bid in current_bidvalues]))

            # logger.debug("*******players not bidded**** %s",  players_not_bidded)
            fake_bid_list = []
            for nb in players_not_bidded:
                get_prev = None
                for prev_bid in prev_bidvalues:
                    if prev_bid.player_id == nb and prev_bid.no_of_turn == turn - 1:
                        get_prev = prev_bid
                        break

                #get_prev = BidValues.objects.get(game_id=gameid, no_of_turn=turn - 1, player_id=nb)

                fake_bid = BidValues()
                fake_bid.game = game
                fake_bid.player_id = nb
                fake_bid.value_a2b = get_prev.value_a2b
                fake_bid.value_b2a = get_prev.value_b2a
                fake_bid.no_of_turn = turn
                # fake_bid=BidValues()
                # fake_bid.value_a2b=get_prev.value_a2b
                if not BidValues.objects.filter(game=game, no_of_turn=turn, player_id=nb).count():
                    fake_bid_list.append(fake_bid)

            BidValues.objects.bulk_create(fake_bid_list)

    #get_new_bids = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
    available_tucks = math.floor(0.90 * game.no_of_trucks * total_no_players)

    a2b = {}

    total_rewards = 0
    data_fleet_awarded = {}
    for i in current_bidvalues:
        a2b[i.player_id] = i.value_a2b
        total_rewards += i.value_a2b
        fleet_size = calculate_fleet_size( turn, i.player_id, game, game_simulation_values)
        data_fleet_awarded.setdefault(i.value_a2b, []).append(
            {'player': i.player_id, 'a2b': i.value_a2b, 'old_fleet_size': math.floor(fleet_size), 'fleet_size': 0})

    # logger.debug("data_fleet_awarded : %s" % data_fleet_awarded)
    # logger.debug("avaialbl trucks: %s" % available_tucks)

    data_fleet_awarded = calculate_awards(data_fleet_awarded, game.brokerage_fee, available_tucks)
    data = {i: j['fleet_size'] for i in a2b for k, v in data_fleet_awarded.items() for j in v if i == j['player']}
    return data


def award_B2A(game, turn, total_no_players, prev_bidvalues=[], current_bidvalues=[], game_simulation_values=[]):
    '''
    :param game: An object of Game
    :param turn: current turn number
    :param total_no_players: number of players in the game
    :param prev_bidvalues: A list of BidValues object
    :param current_bidvalues: A list of BidValues object
    :param game_simulation_values: A list of Game Simulation objects
    :return:
    '''
    #game_table = cache.get("GameDetails%s" % gameid) or Game.objects.get(id=gameid)
    if turn > 1:
        #get_previous_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn - 1)

        #get_bid_values = BidValues.objects.filter(game_id=gameid, no_of_turn=turn)
        # logger.debug("^^^^^^^^^^^^^^^^^^^ %s ^^^^^^^^^^^^^^^^^" % get_bid_values)
        # logger.debug("^^^^^^^************ %s *******^^^^^" % get_previous_values)

        if len(prev_bidvalues) > len(current_bidvalues):
            players_last_turn = []
            players_not_bidded = []
            for prev_bid in prev_bidvalues:
                players_last_turn.append(prev_bid.player_id)

            for curr_bid in current_bidvalues:
                each_player = curr_bid.player_id
                if players_last_turn.count(each_player) == 0:
                    players_not_bidded.append(each_player)

            # logger.debug("*******players not bidded****"+ players_not_bidded)
            fake_bid_list = []
            for nb in players_not_bidded:
                #get_prev = BidValues.objects.get(game_id=gameid, no_of_turn=turn - 1, player_id=nb)
                get_prev = None
                for prev_bid in prev_bidvalues:
                    if prev_bid.player_id == nb and prev_bid.no_of_turn == turn - 1:
                        get_prev = prev_bid
                        break

                fake_bid = BidValues()
                fake_bid.game = game
                fake_bid.player_id = nb
                fake_bid.value_a2b = get_prev.value_a2b
                fake_bid.value_b2a = get_prev.value_b2a
                fake_bid.no_of_turn = turn
                # fake_bid.value_b2a=get_prev.value_b2a
                if not BidValues.objects.filter(game=game, no_of_turn=turn, player_id=nb).count():
                    #fake_bid.save()
                    fake_bid_list.append(fake_bid)

            BidValues.objects.bulk_create(fake_bid_list)

    get_new_bids = current_bidvalues
    available_tucks = math.floor((0.9 * game.no_of_trucks * total_no_players) * 0.8)

    a2b = {}
    total_rewards = 0
    data_fleet_awarded = {}
    for i in get_new_bids:
        a2b[i.player_id] = i.value_b2a
        total_rewards += i.value_b2a
        fleet_size = calculate_fleet_size( turn, i.player_id, game, game_simulation_values)
        data_fleet_awarded.setdefault(i.value_b2a, []).append(
            {'player': i.player_id, 'a2b': i.value_b2a, 'old_fleet_size': math.floor(fleet_size), 'fleet_size': 0})
    # get_fleet_info=FleetNetContribution.objects.filter(game_id=gameid,no_of_turn=turn-1)
    # data_fleet_awarded = sorted(, key=lambda x:x['a2b'])
    # logger.debug("data_fleet_awarded : %s" % data_fleet_awarded)
    # logger.debug("avaialbl trucks: %s" % available_tucks)

    data_fleet_awarded = calculate_awards(data_fleet_awarded, game.brokerage_fee, available_tucks)

    data = {i: j['fleet_size'] for i in a2b for k, v in data_fleet_awarded.items() for j in v if i == j['player']}
    return data