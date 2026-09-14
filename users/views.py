from django.shortcuts import render, redirect, get_object_or_404
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

    followers_count = Follow.objects.filter(
        following=request.user
    ).count()

    following_count = Follow.objects.filter(
        follower=request.user
    ).count()

    return render(
        request,
        'users/profile.html',
        {
            'profile': profile,
            'followers_count': followers_count,
            'following_count': following_count
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


def get_friend_request(user1, user2):

    return FriendRequest.objects.filter(
        sender=user1,
        receiver=user2
    ).first() or FriendRequest.objects.filter(
        sender=user2,
        receiver=user1
    ).first()


def get_friend_status(viewer, target):

    if viewer == target:

        return {
            'friend_request': None,
            'is_friend': False,
            'pending_outgoing': False,
            'pending_incoming': False
        }

    friend_request = get_friend_request(
        viewer,
        target
    )

    is_friend = (
        friend_request is not None
        and friend_request.accepted
    )

    pending_outgoing = (
        friend_request is not None
        and not friend_request.accepted
        and friend_request.sender == viewer
    )

    pending_incoming = (
        friend_request is not None
        and not friend_request.accepted
        and friend_request.receiver == viewer
    )

    return {
        'friend_request': friend_request,
        'is_friend': is_friend,
        'pending_outgoing': pending_outgoing,
        'pending_incoming': pending_incoming
    }


def user_profile(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    followers_count = Follow.objects.filter(
        following=user
    ).count()

    following_count = Follow.objects.filter(
        follower=user
    ).count()

    is_following = False
    target_follows_viewer = False

    friend_request = None
    is_friend = False
    pending_outgoing = False
    pending_incoming = False

    if request.user.is_authenticated and request.user != user:

        friend_status = get_friend_status(
            request.user,
            user
        )

        friend_request = friend_status['friend_request']
        is_friend = friend_status['is_friend']
        pending_outgoing = friend_status['pending_outgoing']
        pending_incoming = friend_status['pending_incoming']

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

            'is_friend': is_friend,
            'pending_outgoing': pending_outgoing,
            'pending_incoming': pending_incoming,

            'followers_count': followers_count,
            'following_count': following_count,

            'is_following': is_following,
            'target_follows_viewer': target_follows_viewer
        }
    )


def send_friend_request(request, username):

    if not request.user.is_authenticated:
        return redirect('login')

    receiver = get_object_or_404(
        User,
        username=username
    )

    if receiver == request.user:
        return redirect('profile')

    existing_request = get_friend_request(
        request.user,
        receiver
    )

    if existing_request:

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

    receiver = get_object_or_404(
        User,
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

    target = get_object_or_404(
        User,
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
    ).select_related(
        'sender',
        'friend_request'
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
        ).exclude(
            id=request.user.id
        ).order_by(
            'username'
        )

    user_results = []

    for user in users:

        friend_status = get_friend_status(
            request.user,
            user
        ) if request.user.is_authenticated else {
            'friend_request': None,
            'is_friend': False,
            'pending_outgoing': False,
            'pending_incoming': False
        }

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

        user_results.append(
            {
                'user': user,
                'profile': getattr(
                    user,
                    'userprofile',
                    None
                ),

                'friend_request': friend_status[
                    'friend_request'
                ],

                'is_friend': friend_status[
                    'is_friend'
                ],

                'pending_outgoing': friend_status[
                    'pending_outgoing'
                ],

                'pending_incoming': friend_status[
                    'pending_incoming'
                ],

                'is_following': is_following,

                'target_follows_viewer': target_follows_viewer
            }
        )

    return render(
        request,
        'users/explore.html',
        {
            'users': user_results,
            'search': search
        }
    )


def followers(request, username=None):

    if username:

        target_user = get_object_or_404(
            User,
            username=username
        )

    else:

        if not request.user.is_authenticated:
            return redirect('login')

        target_user = request.user

    follower_users = User.objects.filter(
        following__following=target_user
    ).distinct().order_by(
        'username'
    )

    return render(
        request,
        'users/followers.html',
        {
            'target_user': target_user,
            'connection_users': follower_users,
            'connection_type': 'Followers'
        }
    )


def following(request, username=None):

    if username:

        target_user = get_object_or_404(
            User,
            username=username
        )

    else:

        if not request.user.is_authenticated:
            return redirect('login')

        target_user = request.user

    following_users = User.objects.filter(
        following__follower=target_user
    ).distinct().order_by(
        'username'
    )

    return render(
        request,
        'users/following.html',
        {
            'target_user': target_user,
            'connection_users': following_users,
            'connection_type': 'Following'
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