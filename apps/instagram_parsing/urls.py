from django.urls import path
from .views import FetchInstagramProfile

urlpatterns = [
    path('fetch/', FetchInstagramProfile.as_view(), name='fetch-instagram-profile'),
]
