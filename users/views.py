from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from .forms import UserProfileForm
from .models import UserProfile, Notification, FriendRequest, Follow


def home(request):

    return render(
        request,
        'users/home.html'
    )


def profile(request):

    if not request.user.is_authenticated:
        return redirect('login')

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        'users/profile.html',
        {
            'profile': profile
        }
    )


def edit_profile(request):

    if not request.user.is_authenticated:
        return redirect('login')

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():

            form.save()

            return redirect('profile')

    else:

        form = UserProfileForm(
            instance=profile
        )

    return render(
        request,
        'users/edit_profile.html',
        {
            'form': form
        }
    )


def user_profile(request, username):

    user = User.objects.get(
        username=username
    )

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    friend_request = None

    if request.user.is_authenticated:

        friend_request = FriendRequest.objects.filter(
            sender=request.user,
            receiver=user
        ).first()

    followers_count = Follow.objects.filter(
        following=user
    ).count()

    following_count = Follow.objects.filter(
        follower=user
    ).count()

    is_following = False
    target_follows_viewer = False

    if request.user.is_authenticated:

        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()

        target_follows_viewer = Follow.objects.filter(
            follower=user,
            following=request.user
        ).exists()

    return render(
        request,
        'users/user_profile.html',
        {
            'profile': profile,
            'profile_user': user,
            'friend_request': friend_request,
            'followers_count': followers_count,
            'following_count': following_count,
            'is_following': is_following,
            'target_follows_viewer': target_follows_viewer
        }
    )


def send_friend_request(request, username):

    if not request.user.is_authenticated:
        return redirect('login')

    receiver = User.objects.get(
        username=username
    )

    if receiver == request.user:
        return redirect('profile')

    friend_request = FriendRequest.objects.filter(
        sender=request.user,
        receiver=receiver
    ).first()

    if friend_request:

        return redirect(
            'user_profile',
            username=username
        )

    friend_request = FriendRequest.objects.create(
        sender=request.user,
        receiver=receiver
    )

    Notification.objects.create(
        recipient=receiver,
        sender=request.user,
        notification_type='friend_request',
        message=f'@{request.user.username} sent you a friend request',
        friend_request=friend_request
    )

    return redirect(
        'user_profile',
        username=username
    )


def cancel_friend_request(request, username):

    if not request.user.is_authenticated:
        return redirect('login')

    receiver = User.objects.get(
        username=username
    )

    FriendRequest.objects.filter(
        sender=request.user,
        receiver=receiver,
        accepted=False
    ).delete()

    return redirect(
        'user_profile',
        username=username
    )


def follow_user(request, username):

    if not request.user.is_authenticated:
        return redirect('login')

    target = User.objects.get(
        username=username
    )

    if target == request.user:
        return redirect('profile')

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target
    )

    if created:

        Notification.objects.create(
            recipient=target,
            sender=request.user,
            notification_type='follow',
            message=f'You have a new follower: @{request.user.username}'
        )

    return redirect(
        'user_profile',
        username=username
    )


def notifications(request):

    if not request.user.is_authenticated:
        return redirect('login')

    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by(
        '-created_at'
    )

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    return render(
        request,
        'users/notifications.html',
        {
            'notifications': notifications
        }
    )


def accept_friend_request(request, request_id):

    if not request.user.is_authenticated:
        return redirect('notifications')

    friend_request = FriendRequest.objects.filter(
        id=request_id,
        receiver=request.user,
        accepted=False
    ).first()

    if friend_request is None:
        return redirect('notifications')

    friend_request.accepted = True
    friend_request.save()

    Follow.objects.get_or_create(
        follower=friend_request.sender,
        following=friend_request.receiver
    )

    Notification.objects.create(
        recipient=friend_request.sender,
        sender=request.user,
        notification_type='friend_accepted',
        message=f'@{request.user.username} accepted your friend request'
    )

    return redirect(
        'notifications'
    )


def decline_friend_request(request, request_id):

    if not request.user.is_authenticated:
        return redirect('notifications')

    friend_request = FriendRequest.objects.filter(
        id=request_id,
        receiver=request.user,
        accepted=False
    ).first()

    if friend_request is None:
        return redirect('notifications')

    friend_request.delete()

    return redirect(
        'notifications'
    )


def explore(request):

    search = request.GET.get(
        'search',
        ''
    ).strip()

    users = User.objects.none()

    if search:

        users = User.objects.filter(
            is_active=True,
            username__icontains=search
        ).order_by(
            'username'
        )

    return render(
        request,
        'users/explore.html',
        {
            'users': users,
            'search': search
        }
    )


def register(request):

    if request.method == 'POST':

        form = UserProfileForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if User.objects.filter(
                username=username
            ).exists():

                return render(
                    request,
                    'users/register.html',
                    {
                        'form': form,
                        'error': 'Username already exists.'
                    }
                )

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            profile = form.save(
                commit=False
            )

            profile.user = user
            profile.save()

            return render(
                request,
                'users/register.html',
                {
                    'form': UserProfileForm(),
                    'success': 'Account created successfully!'
                }
            )

    else:

        form = UserProfileForm()

    return render(
        request,
        'users/register.html',
        {
            'form': form
        }
    )


def user_login(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            return redirect('home')

        return render(
            request,
            'users/login.html',
            {
                'error': 'Invalid username or password.'
            }
        )

    return render(
        request,
        'users/login.html'
    )


def user_logout(request):

    logout(request)

    return redirect(
        'home'
    )