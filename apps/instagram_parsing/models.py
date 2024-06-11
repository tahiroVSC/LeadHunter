from django.db import models

class InstagramProfile(models.Model):
    username = models.CharField(max_length=255, unique=True)
    mediacount = models.IntegerField()
    followers = models.IntegerField()
    followees = models.IntegerField()
    biography = models.TextField()
    profile_pic_url = models.CharField(max_length=255)

class InstagramPost(models.Model):
    username = models.CharField(max_length=255)
    post_data = models.JSONField()
    profile_pic_url = models.CharField(max_length=255)

class InstagramComment(models.Model):
    post = models.ForeignKey(InstagramPost, related_name='comments', on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    text = models.TextField()
    date = models.DateTimeField()
    user_profile = models.CharField(max_length=255)


class InstaParsRequest(models.Model):
    username =  models.CharField( max_length= 255)