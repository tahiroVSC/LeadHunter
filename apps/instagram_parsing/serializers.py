from rest_framework import serializers
from .models import InstagramProfile, InstagramPost, InstagramComment,InstaParsRequest

class InstagramProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramProfile
        fields = '__all__'

class InstagramPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramPost
        fields = '__all__'

class InstagramCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramComment
        fields = '__all__'


class InstaParsRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstaParsRequest
        fields = '__all__'