from django.contrib import admin
from .models import *
from .models import Game
# from djcelery.models import TaskMeta
# class TaskMetaAdmin(admin.ModelAdmin):
#     readonly_fields = ('result',)
# admin.site.register(TaskMeta, TaskMetaAdmin)
admin.site.register(Game)
admin.site.register(UserProfile)
admin.site.register(UserGameRecords)
admin.site.register(GameSimulationDetails)
admin.site.register(WinnerTable)
admin.site.register(TurnAlert)
admin.site.register(FleetNetContribution)
admin.site.register(Notify)
admin.site.register(BidValues)

