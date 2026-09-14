"""
URL configuration for GET project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from users import views


urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'profile/edit/',
        views.edit_profile,
        name='edit_profile'
    ),

    path(
        'profile/followers/',
        views.followers,
        name='profile_followers'
    ),

    path(
        'profile/following/',
        views.following,
        name='profile_following'
    ),

    path(
        'user/<str:username>/',
        views.user_profile,
        name='user_profile'
    ),

    path(
        'user/<str:username>/followers/',
        views.followers,
        name='user_followers'
    ),

    path(
        'user/<str:username>/following/',
        views.following,
        name='user_following'
    ),

    path(
        'user/<str:username>/add-friend/',
        views.send_friend_request,
        name='send_friend_request'
    ),

    path(
        'user/<str:username>/cancel-friend/',
        views.cancel_friend_request,
        name='cancel_friend_request'
    ),

    path(
        'user/<str:username>/follow/',
        views.follow_user,
        name='follow_user'
    ),

    path(
        'notifications/',
        views.notifications,
        name='notifications'
    ),

    path(
        'notifications/<int:request_id>/accept/',
        views.accept_friend_request,
        name='accept_friend_request'
    ),

    path(
        'notifications/<int:request_id>/decline/',
        views.decline_friend_request,
        name='decline_friend_request'
    ),

    path(
        'explore/',
        views.explore,
        name='explore'
    ),

    path(
        'register/',
        views.register,
        name='register'
    ),

    path(
        'login/',
        views.user_login,
        name='login'
    ),

    path(
        'logout/',
        views.user_logout,
        name='logout'
    ),
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )