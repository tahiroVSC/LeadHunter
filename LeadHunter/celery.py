# LeadHunter/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Установите переменную окружения для Django настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LeadHunter.settings')

app = Celery('LeadHunter')

# Используйте строку конфигурации из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживайте задачи в установленных приложениях Django
app.autodiscover_tasks()