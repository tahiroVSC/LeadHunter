from celery import shared_task
from .models import InstagramProfile, InstagramPost, InstagramComment
from .views import FetchInstagramProfile
import asyncio

@shared_task
def check_new_posts():
    profiles = InstagramProfile.objects.all()
    fetcher = FetchInstagramProfile()

    for profile in profiles:
        username = profile.username
        new_posts_data, _ = fetcher.fetch_and_save_profile(username)

        for post_data in new_posts_data:
            existing_post = InstagramPost.objects.filter(
                username=username, 
                post_data__date=post_data['post_data']['date']
            ).first()

            if not existing_post:
                post_instance = InstagramPost.objects.create(
                    username=username,
                    post_data=post_data['post_data'],
                    profile_pic_url=post_data['profile_pic_url']
                )

                for comment_data in post_data['post_data']['comments']:
                    InstagramComment.objects.create(
                        post=post_instance,
                        username=comment_data['username'],
                        text=comment_data['text'],
                        date=comment_data['date']
                    )
                
                # Удаление старых постов, если их больше 10
                posts_count = InstagramPost.objects.filter(username=username).count()
                if posts_count > 10:
                    oldest_posts = InstagramPost.objects.filter(username=username).order_by('post_data__date')[:posts_count - 10]
                    oldest_posts.delete()