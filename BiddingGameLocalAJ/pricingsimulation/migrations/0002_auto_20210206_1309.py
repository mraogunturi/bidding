# Generated by Django 3.0.6 on 2021-02-06 13:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pricingsimulation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='force_timestamp',
            field=models.DateTimeField(default=datetime.datetime(2021, 2, 7, 13, 9, 43, 462703)),
        ),
    ]
