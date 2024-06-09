# apps/instagram_app/tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def parse_instagram_profiles_task():
    call_command('parse_instagram_profiles')
