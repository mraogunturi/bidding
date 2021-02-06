#!/bin/bash
cd /usr/sbin
./rabbitmq-server restart
#cd /opt/pricing/pricing
cd /pricing_simulation_verison1_localgit\pricing
#pip install -U https://github.com/celery/celery/zipball/3.1#egg=celery
#cd /opt/pricing/pricing
python manage.py makemigrations
python manage.py migrate
export C_FORCE_ROOT="true"
truncate celerybeat.pid --size 0
celery -A pricing worker & > ./celery_output.log &
python manage.py runserver 0.0.0.0:9000 --noreload & > ./django_output.log &
celery beat -A pricing
