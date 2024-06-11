import os
import random
import asyncio
import aiohttp
import instaloader
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import InstagramPost, InstagramProfile, InstagramComment
from .serializers import InstagramPostSerializer, InstagramProfileSerializer, InstaParsRequestSerializer

class SessionManager:
    def __init__(self, accounts):
        self.accounts = accounts
        self.sessions = []

    async def login_all(self):
        tasks = [self.login(account) for account in self.accounts]
        self.sessions = await asyncio.gather(*tasks)

    async def login(self, account):
        ig = instaloader.Instaloader()
        session_file = f"{account['username']}.session"
        if os.path.exists(session_file):
            ig.load_session_from_file(account['username'], session_file)
        else:
            ig.context.log("Logging in new session")
            try:
                ig.login(account['username'], account['password'])
                ig.save_session_to_file(session_file)
            except Exception as e:
                ig.context.log(f"Failed to login for {account['username']}: {e}")
        return ig

class FetchInstagramProfile(APIView):
    serializer_class = InstaParsRequestSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = [
            {"username": "instaloader224", "password": "Abu20075"},
            {"username": "instaloader_226", "password": "Abu20075"},
            {"username": "instaloader_211", "password": "Abu20075"},
        ]
        self.session_manager = SessionManager(self.accounts)
        asyncio.run(self.session_manager.login_all())

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
        account_index = random.randint(0, len(self.session_manager.sessions) - 1)
        ig = self.session_manager.sessions[account_index]

        async with aiohttp.ClientSession() as session:
            try:
                profile = instaloader.Profile.from_username(ig.context, username)
            except Exception as e:
                print(f"Error loading profile for {username}: {e}")
                return [], {}

            image_dir = os.path.join(settings.MEDIA_ROOT, 'images')
            await self.ensure_directory_exists(image_dir)

            profile_pic_url = profile.profile_pic_url
            profile_pic_filename = f"{username}_profilefoto.jpg"
            profile_pic_path = os.path.join(image_dir, profile_pic_filename)
            try:
                await self.save_image(session, profile_pic_url, profile_pic_path)
            except Exception as e:
                print(f"Error saving profile picture: {e}")

            posts_data = []
            tasks = []

            for index, post in enumerate(profile.get_posts(), start=1):
                if index > post_count:
                    break

                tasks.append(self.process_post(session, post, username, image_dir, profile_pic_filename, index))

            posts_data = await asyncio.gather(*tasks)

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
            image_name = f"{username}_post_{index}_image.jpg"
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
                image_name = f"{username}_post_{index}_image_{i}.jpg"
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
        new_posts, profile_info = loop.run_until_complete(self.fetch_and_save_profile_async(username, post_count))
        loop.close()

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

        for post in new_posts:
            post_instance, created = InstagramPost.objects.get_or_create(
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

        posts = InstagramPost.objects.filter(username=username)[:post_count]
        profile_serializer = InstagramProfileSerializer(profile)
        post_serializer = InstagramPostSerializer(posts, many=True)
        return Response({"profile": profile_serializer.data, "posts": post_serializer.data}, status=status.HTTP_200_OK)

    def fetch_profile_from_db(self, username, post_count):
        profile = InstagramProfile.objects.filter(username=username).first()
        if profile:
            posts = InstagramPost.objects.filter(username=username)[:post_count]
            profile_serializer = InstagramProfileSerializer(profile)
            post_serializer = InstagramPostSerializer(posts, many=True)
            return Response({"profile": profile_serializer.data, "posts": post_serializer.data}, status=status.HTTP_200_OK)
        return None

    def get(self, request, *args, **kwargs):
        username = request.query_params.get('username')
        if not username:
            return Response({"error": "Username parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        post_count = int(request.query_params.get('post_count', 10))
        db_response = self.fetch_profile_from_db(username)
        if db_response is not None:
            return db_response
        return self.fetch_and_save_profile(username, post_count)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            post_count = serializer.validated_data.get('post_count', 10)
            db_response = self.fetch_profile_from_db(username, post_count)
            if db_response is not None:
                return db_response
            return self.fetch_and_save_profile(username, post_count)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

