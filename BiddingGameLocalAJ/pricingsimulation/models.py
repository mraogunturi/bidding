from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
import datetime
#from celery import worker

from django.core.validators import MinValueValidator


class UserProfile(models.Model):
    STATUS_CHOICES = (
        ('T', 'True'),
        ('F', 'False'),
    )
    user = models.OneToOneField(User, related_name='user_profile', db_index = True, on_delete=models.CASCADE)
    company = models.CharField(max_length=50)
    terms_condition = models.CharField(choices=STATUS_CHOICES, max_length=1)
    activation_key = models.CharField(max_length=40, blank=True ,null=True)
    key_expires = models.DateTimeField(default=now)
    is_alive = models.BooleanField(default=False)
    is_ai_player = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email


class Game(models.Model):
    STATUS_CHOICES = (
        ('S', 'Start'),
        ('E', 'End'),
        ('P', 'Pending'),
        ('R', 'Result in Progress'),
    )
    user = models.ForeignKey(User, related_name="user_id", db_index=True,on_delete=models.CASCADE )
    name = models.CharField(blank=False, unique=False,null=False,max_length=50)
    start_date_time = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    end_date_time = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    game_status = models.CharField(choices=STATUS_CHOICES, max_length=1, default='P', db_index=True)
    number_of_players = models.PositiveIntegerField(validators=[MinValueValidator(2)])
    no_of_trucks = models.PositiveIntegerField(default=25)
    no_of_turns_per_player = models.PositiveIntegerField(default=5)
    shrink_ratio = models.FloatField(default=0.85)
    growth_ratio = models.FloatField(default=1.1)
    empty_cost_per_truck = models.BigIntegerField(default=400)
    loaded_cost_per_truck = models.BigIntegerField(default=550)
    unused_capital_cost_perTruck = models.BigIntegerField(default=250)
    created_date = models.DateTimeField(default=now, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_ai = models.BooleanField(default=False, db_index=True)
    no_of_ai_player = models.PositiveIntegerField(blank=True, null=True)
    no_of_normal_players = models.PositiveIntegerField(default=2 )
    total_trucks_AvailableA2B = models.BigIntegerField(blank=True, default=50, null=True)
    total_trucks_AvailableB2A = models.BigIntegerField(blank=True, default=50, null=True)
    force_t2 = models.BooleanField(default=False)
    force_timestamp=models.DateTimeField(default=datetime.datetime.now()+ datetime.timedelta(days=1))
    brokerage_fee = models.BigIntegerField(default=1200)
    # creator_is_play=models.BigAutoField(default=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ('-start_date_time',)


class Notify(models.Model):
    STATUS_CHOICES = (
        ('F', 'Switch to turn1'),
        ('S', 'Switch to turn2'),
        )
    game = models.ForeignKey(Game, related_name="game_notify", on_delete=models.CASCADE)
    msg = models.CharField(choices=STATUS_CHOICES, max_length=1, default='F')
    def __str__(self):
        return str(self.game)


class UserGameRecords(models.Model):
    STATUS_CHOICES = (
        ('J', 'Join'),
        ('B',' Bid'),
        ('I','Incomplete'),
        ('T','Turn2'),
        ('Q', 'Quit'),
        ('E', 'End'),
    )
    game = models.ForeignKey(Game, related_name="user_game_record", db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_of_game", db_index=True, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, max_length=1, default='E', db_index=True)
    no_of_turns_completed = models.IntegerField(default=0)
    user_nick_name = models.CharField(max_length=50, default='')

    def __str__(self):
        return self.user.email


class BidValues(models.Model):
    game = models.ForeignKey(Game, related_name="game_sess", db_index=True, on_delete=models.CASCADE)
    player = models.ForeignKey(User, related_name="user_session", db_index=True, on_delete=models.CASCADE)
    value_a2b = models.IntegerField()
    value_b2a = models.IntegerField()
    no_of_turn = models.IntegerField(default=1, db_index=True)
    time_stamp = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.id)


class GameSimulationDetails(models.Model):
    game = models.ForeignKey(Game, related_name="game_session", db_index=True, on_delete=models.CASCADE)
    player = models.ForeignKey(User, related_name="player", db_index=True, on_delete=models.CASCADE)
    value_a2b = models.IntegerField(default=None)
    value_b2a = models.IntegerField(default=None)
    no_of_turn = models.IntegerField(default=1)
    trucks_a2b_Awarded = models.IntegerField(default=12)
    trucks_b2a_Awarded = models.IntegerField(default=15)
    trucks_max_awarded = models.IntegerField(default=0)
    revenue = models.BigIntegerField(default=15)

    loaded_cost = models.BigIntegerField(default=12)
    empty_cost = models.BigIntegerField(default=12)
    net_contribution = models.IntegerField(default=15)
    contribution_per_load = models.IntegerField(default=15)
    loaded_ratio = models.FloatField(default=15)
    bid_date_time = models.DateTimeField(default=now)
    sum_of_all_bids = models.IntegerField(blank=True, null=True)
    ratio_of_multiplication = models.FloatField(blank=True, null=True)
    simulation_timestamp=models.DateTimeField(default=datetime.datetime.now)
    fleet_size = models.IntegerField(blank=True, null=True,default=None)

    def __str__(self):
        a=self.game_id+ self.player_id+self.no_of_turn
        return str(a)
# class Celery_Tasks(models.Models):
#     task=models.ForeignKey()


class FleetNetContribution(models.Model):
    game = models.ForeignKey(Game, related_name="game_fleet", db_index=True, on_delete=models.CASCADE)
    player = models.ForeignKey(User, related_name="player_fleet", db_index=True, on_delete=models.CASCADE)
    trucks_max_awarded = models.IntegerField(default=15)
    net_contribution = models.IntegerField(default=0)
    no_of_turn = models.IntegerField(default=1)

    def __str__(self):
        a=self.id+self.player_id+self.no_of_turn
        return str(a)


class TurnAlert(models.Model):
    STATUS_CHOICES = (
        ('S', 'Success'),
        ('F', 'Fail'),
    )
    game = models.ForeignKey(Game, db_index=True, on_delete=models.CASCADE)
    turn_no = models.IntegerField(default=0, db_index=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=1, default='F', db_index=True)
    time_Stamp=models.DateTimeField(default=now)
    def __str__(self):
        return str(self.id)

class WinnerTable(models.Model):
    game = models.ForeignKey(Game, db_index=True, on_delete=models.CASCADE)
    player = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    player_total_net_contribution = models.IntegerField()
    player_rank = models.IntegerField(db_index=True)
    user_nick_name = models.CharField(max_length=50, default='')

    def __str__(self):
        return str(self.id)
