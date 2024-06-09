# apps/instagram_parsing/management/commands/parse_instagram_profiles.py
import asyncio
from django.core.management.base import BaseCommand
from apps.instagram_parsing.models import InstagramProfile, InstagramPost, InstagramComment
from apps.instagram_parsing.views import FetchInstagramProfile

class Command(BaseCommand):
    help = 'Fetch and update Instagram profiles'

    def handle_profile(self, profile):
        fetcher = FetchInstagramProfile()
        posts_data, profile_info = fetcher.fetch_and_save_profile(profile.username, post_count=10)

        InstagramProfile.objects.update_or_create(
            username=profile_info['username'],
            defaults={
                'mediacount': profile_info['mediacount'],
                'followers': profile_info['followers'],
                'followees': profile_info['followees'],
                'biography': profile_info['biography'],
                'profile_pic_url': profile_info['profile_pic_url']
            }
        )

        for post in posts_data:
            post_instance, created = InstagramPost.objects.update_or_create(
                username=profile.username,
                post_data=post['post_data'],
                defaults={'profile_pic_url': profile_info['profile_pic_url']}
            )
            for comment_data in post['post_data']['comments']:
                InstagramComment.objects.update_or_create(
                    post=post_instance,
                    username=comment_data['username'],
                    defaults={
                        'text': comment_data['text'],
                        'date': comment_data['date']
                    }
                )

        # Удаляем старые посты, оставляя только последние 10
        InstagramPost.objects.filter(username=profile.username).order_by('-id')[10:].delete()

    def handle(self, *args, **kwargs):
        profiles = InstagramProfile.objects.all()
        for profile in profiles:
            self.handle_profile(profile)
