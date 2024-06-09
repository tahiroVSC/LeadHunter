from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import InstagramPost, InstagramProfile, InstagramComment
from .serializers import InstagramPostSerializer, InstagramProfileSerializer
import instaloader
import os
import aiohttp
import asyncio
import time
import random
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class FetchInstagramProfile(APIView):
    serializer_class = InstagramPostSerializer

    async def ensure_directory_exists(self, directory_path):
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

    async def save_image(self, session, image_url, save_path):
        async with session.get(image_url) as response:
            data = await response.read()
            with open(save_path, 'wb') as f:
                f.write(data)

    async def save_video(self, session, video_url, save_path):
        async with session.get(video_url) as response:
            data = await response.read()
            with open(save_path, 'wb') as f:
                f.write(data)

    async def fetch_and_save_profile_async(self, username, post_count=10):
        async with aiohttp.ClientSession() as session:
            ig = instaloader.Instaloader()
            ig.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
            profile = instaloader.Profile.from_username(ig.context, username)
            image_dir = os.path.join(settings.MEDIA_ROOT, 'images')
            await self.ensure_directory_exists(image_dir)

            profile_pic_url = profile.profile_pic_url
            profile_pic_filename = f"{username}_profilefoto.png"
            profile_pic_path = os.path.join(image_dir, profile_pic_filename)
            try:
                await self.save_image(session, profile_pic_url, profile_pic_path)
            except Exception as e:
                print(f"Error saving profile picture: {e}")

            posts_data = []
            tasks = []  # List to hold all async tasks

            for index, post in enumerate(profile.get_posts(), start=1):
                if index > post_count:
                    break

                tasks.append(self.process_post(session, post, username, image_dir, profile_pic_filename, index))
                
            posts_data = await asyncio.gather(*tasks)  # Run all tasks concurrently

            profile_info = {
                "username": profile.username,
                "mediacount": profile.mediacount,
                "followers": profile.followers,
                "followees": profile.followees,
                "biography": profile.biography,
                "profile_pic_url": os.path.join('images', profile_pic_filename)
            }

            return posts_data, profile_info

    async def process_post(self, session, post, username, image_dir, profile_pic_filename, index):
        post_data = {
            "username": username,
            "post_data": {
                "date": str(post.date_utc),
                "likes": post.likes,
                "caption": post.caption,
                "images": [],
                "videos": [],
                "comments": []
            },
            "profile_pic_url": os.path.join('images', profile_pic_filename)
        }

        if post.is_video:
            video_url = post.video_url
            video_name = f"{username}_post_{index}_video.mp4"
            video_path = os.path.join(image_dir, video_name)
            try:
                await self.save_video(session, video_url, video_path)
                post_data["post_data"]["videos"].append({
                    "video_url": video_url,
                    "video_filename": video_name
                })
            except Exception as e:
                print(f"Error saving post video {video_name}: {e}")
        else:
            image_url = post.url
            image_name = f"{username}_post_{index}_image.png"
            image_path = os.path.join(image_dir, image_name)
            try:
                await self.save_image(session, image_url, image_path)
                post_data["post_data"]["images"].append({
                    "image_url": image_url,
                    "image_filename": image_name
                })
            except Exception as e:
                print(f"Error saving post image {image_name}: {e}")

        for i, sidecar in enumerate(post.get_sidecar_nodes(), start=1):
            if sidecar.is_video:
                video_url = sidecar.video_url
                video_name = f"{username}_post_{index}_video_{i}.mp4"
                video_path = os.path.join(image_dir, video_name)
                try:
                    await self.save_video(session, video_url, video_path)
                    post_data["post_data"]["videos"].append({
                        "video_url": video_url,
                        "video_filename": video_name
                    })
                except Exception as e:
                    print(f"Error saving post video {video_name}: {e}")
            else:
                image_url = sidecar.display_url
                image_name = f"{username}_post_{index}_image_{i}.png"
                image_path = os.path.join(image_dir, image_name)
                try:
                    await self.save_image(session, image_url, image_path)
                    post_data["post_data"]["images"].append({
                        "image_url": image_url,
                        "image_filename": image_name
                    })
                except Exception as e:
                    print(f"Error saving post image {image_name}: {e}")

        try:
            comments = post.get_comments()
            for comment in comments:
                comment_data = {
                    "username": comment.owner.username,
                    "text": comment.text,
                    "date": str(comment.created_at_utc),
                    "user_profile": f"https://www.instagram.com/{comment.owner.username}/"
                }
                post_data["post_data"]["comments"].append(comment_data)
        except instaloader.exceptions.QueryReturnedBadRequestException as e:
            print(f"Error fetching comments for post {index}: {e}")

        return post_data

    def fetch_and_save_profile(self, username, post_count=10):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.fetch_and_save_profile_async(username, post_count))
        loop.close()
        return result

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)

        profile = InstagramProfile.objects.filter(username=username).first()
        if profile:
            posts = InstagramPost.objects.filter(username=username)[:10]
            profile_serializer = InstagramProfileSerializer(profile)
            post_serializer = InstagramPostSerializer(posts, many=True)
            return Response({"profile": profile_serializer.data, "posts": post_serializer.data}, status=status.HTTP_200_OK)
        else:
            posts_data, profile_info = self.fetch_and_save_profile(username)
            profile, created = InstagramProfile.objects.update_or_create(
                username=username,
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
                    username=username,
                    post_data=post['post_data'],
                    profile_pic_url=post['profile_pic_url']
                )
                for comment_data in post['post_data']['comments']:
                    InstagramComment.objects.create(
                        post=post_instance,
                        username=comment_data['username'],
                        text=comment_data['text'],
                        date=comment_data['date']
                    )

            profile_serializer = InstagramProfileSerializer(profile)
            post_serializer = InstagramPostSerializer(posts_data, many=True)
            return Response({"profile": profile_serializer.data, "posts": post_serializer.data}, status=status.HTTP_200_OK)

