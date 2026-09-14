from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UserProfileForm
from .models import (
    ChatGroup,
    FriendRequest,
    Follow,
    GroupMember,
    GroupMessage,
    GroupMessageRead,
    Message,
    Notification,
    UserProfile
)


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
            instance=profile,
            initial={
                'username': request.user.username,
                'email': request.user.email
            }
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
        Q(
            sender=user1,
            receiver=user2
        ) |
        Q(
            sender=user2,
            receiver=user1
        )
    ).first()


def get_friend_status(user1, user2):

    request_obj = get_friend_request(
        user1,
        user2
    )

    if request_obj is None:

        return {
            'is_friend': False,
            'pending_outgoing': False,
            'pending_incoming': False
        }

    if request_obj.accepted:

        return {
            'is_friend': True,
            'pending_outgoing': False,
            'pending_incoming': False
        }

    return {
        'is_friend': request_obj.sender == user1,
        'pending_outgoing': request_obj.sender == user1,
        'pending_incoming': request_obj.receiver == user1
    }


def user_profile(request, username):

    target_user = get_object_or_404(
        User,
        username=username
    )

    profile, created = UserProfile.objects.get_or_create(
        user=target_user
    )

    followers_count = Follow.objects.filter(
        following=target_user
    ).count()

    following_count = Follow.objects.filter(
        follower=target_user
    ).count()

    is_friend = False
    pending_outgoing = False
    pending_incoming = False
    is_following = False
    target_follows_viewer = False

    if request.user.is_authenticated:

        friend_status = get_friend_status(
            request.user,
            target_user
        )

        is_friend = friend_status['is_friend']
        pending_outgoing = friend_status['pending_outgoing']
        pending_incoming = friend_status['pending_incoming']

        is_following = Follow.objects.filter(
            follower=request.user,
            following=target_user
        ).exists()

        target_follows_viewer = Follow.objects.filter(
            follower=target_user,
            following=request.user
        ).exists()

    return render(
        request,
        'users/user_profile.html',
        {
            'profile': profile,
            'followers_count': followers_count,
            'following_count': following_count,
            'is_friend': is_friend,
            'pending_outgoing': pending_outgoing,
            'pending_incoming': pending_incoming,
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
        return redirect(
            'user_profile',
            username=username
        )

    existing_request = get_friend_request(
        request.user,
        receiver
    )

    if existing_request is None:

        friend_request = FriendRequest.objects.create(
            sender=request.user,
            receiver=receiver
        )

        Notification.objects.create(
            recipient=receiver,
            sender=request.user,
            notification_type='friend_request',
            message=(
                f'@{request.user.username} '
                f'sent you a friend request'
            ),
            friend_request=friend_request,
            target_url=(
                f'/user/{request.user.username}/'
            )
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

    target_user = get_object_or_404(
        User,
        username=username
    )

    if target_user == request.user:
        return redirect('profile')

    Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )

    return redirect(
        'user_profile',
        username=username
    )


def notifications(request):

    if not request.user.is_authenticated:
        return redirect('login')

    notifications_list = Notification.objects.filter(
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
            'notifications': notifications_list
        }
    )


def accept_friend_request(request, request_id):

    if not request.user.is_authenticated:
        return redirect('login')

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=request.user
    )

    friend_request.accepted = True
    friend_request.save()

    Follow.objects.get_or_create(
        follower=friend_request.sender,
        following=friend_request.receiver
    )

    Follow.objects.get_or_create(
        follower=friend_request.receiver,
        following=friend_request.sender
    )

    Notification.objects.create(
        recipient=friend_request.sender,
        sender=request.user,
        notification_type='friend_accepted',
        message=(
            f'@{request.user.username} '
            f'accepted your friend request'
        ),
        target_url=(
            f'/user/{request.user.username}/'
        )
    )

    return redirect('notifications')


def decline_friend_request(request, request_id):

    if not request.user.is_authenticated:
        return redirect('login')

    friend_request = get_object_or_404(
        FriendRequest,
        id=request_id,
        receiver=request.user
    )

    friend_request.delete()

    return redirect('notifications')


def explore(request):

    if not request.user.is_authenticated:
        return redirect('login')

    query = request.GET.get(
        'q',
        ''
    ).strip()

    user_results = []

    if query:

        users = User.objects.filter(
            username__icontains=query
        ).exclude(
            id=request.user.id
        ).order_by(
            'username'
        )

        for user in users:

            profile, created = UserProfile.objects.get_or_create(
                user=user
            )

            friend_status = get_friend_status(
                request.user,
                user
            )

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
                    'profile': profile,
                    'is_friend': friend_status['is_friend'],
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
            'user_results': user_results,
            'query': query
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
            'follower_users': follower_users
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
        followers__follower=target_user
    ).distinct().order_by(
        'username'
    )

    return render(
        request,
        'users/following.html',
        {
            'target_user': target_user,
            'following_users': following_users
        }
    )


# ============================================================
# PRIVATE MESSAGES
# ============================================================

def messages(request):

    if not request.user.is_authenticated:
        return redirect('login')

    sent_to = Message.objects.filter(
        sender=request.user
    ).values_list(
        'receiver_id',
        flat=True
    )

    received_from = Message.objects.filter(
        receiver=request.user
    ).values_list(
        'sender_id',
        flat=True
    )

    user_ids = set(sent_to) | set(received_from)

    conversation_users = []

    for user_id in user_ids:

        user = User.objects.filter(
            id=user_id
        ).first()

        if user is None:
            continue

        profile, created = UserProfile.objects.get_or_create(
            user=user
        )

        last_message = Message.objects.filter(
            Q(
                sender=request.user,
                receiver=user
            ) |
            Q(
                sender=user,
                receiver=request.user
            )
        ).order_by(
            '-created_at'
        ).first()

        unread_count = Message.objects.filter(
            sender=user,
            receiver=request.user,
            is_read=False
        ).count()

        conversation_users.append(
            {
                'user': user,
                'profile': profile,
                'last_message': last_message,
                'unread_count': unread_count
            }
        )

    conversation_users.sort(
        key=lambda item: (
            item['last_message'].created_at
            if item['last_message']
            else 0
        ),
        reverse=True
    )

    groups = ChatGroup.objects.filter(
        members__user=request.user
    ).prefetch_related(
        'members__user'
    ).distinct().order_by(
        '-created_at'
    )

    group_conversations = []

    for group in groups:

        last_message = group.messages.order_by(
            '-created_at'
        ).first()

        unread_count = group.messages.exclude(
            sender=request.user
        ).exclude(
            read_by__user=request.user
        ).count()

        group_conversations.append(
            {
                'group': group,
                'last_message': last_message,
                'unread_count': unread_count
            }
        )

    return render(
        request,
        'users/messages.html',
        {
            'conversation_users': conversation_users,
            'group_conversations': group_conversations
        }
    )


def chat(request, username):

    if not request.user.is_authenticated:
        return redirect('login')

    other_user = get_object_or_404(
        User,
        username=username
    )

    if other_user == request.user:
        return redirect('profile')

    other_profile, created = UserProfile.objects.get_or_create(
        user=other_user
    )

    if request.method == 'POST':

        message_text = request.POST.get(
            'message',
            ''
        ).strip()

        if message_text:

            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                message=message_text
            )

            Notification.objects.create(
                recipient=other_user,
                sender=request.user,
                notification_type='message',
                message=(
                    f'@{request.user.username} '
                    f'sent you a message'
                ),
                target_url=(
                    f'/messages/{request.user.username}/'
                )
            )

        return redirect(
            'chat',
            username=username
        )

    chat_messages = Message.objects.filter(
        Q(
            sender=request.user,
            receiver=other_user
        ) |
        Q(
            sender=other_user,
            receiver=request.user
        )
    ).select_related(
        'sender',
        'receiver'
    ).order_by(
        'created_at'
    )

    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    return render(
        request,
        'users/chat.html',
        {
            'other_user': other_user,
            'other_profile': other_profile,
            'chat_messages': chat_messages
        }
    )


# ============================================================
# GROUP CHAT
# ============================================================

def create_group(request):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':

        group_name = request.POST.get(
            'name',
            ''
        ).strip()

        add_permission = request.POST.get(
            'add_permission',
            ChatGroup.ADD_EVERYONE
        )

        if not group_name:
            return redirect('create_group')

        if add_permission not in dict(
            ChatGroup.ADD_PERMISSION_CHOICES
        ):
            add_permission = ChatGroup.ADD_EVERYONE

        group = ChatGroup.objects.create(
            name=group_name,
            creator=request.user,
            add_permission=add_permission
        )

        GroupMember.objects.create(
            group=group,
            user=request.user
        )

        return redirect(
            'group_chat',
            group_id=group.id
        )

    return render(
        request,
        'users/create_group.html',
        {
            'permission_choices': (
                ChatGroup.ADD_PERMISSION_CHOICES
            )
        }
    )


def group_chat(request, group_id):

    if not request.user.is_authenticated:
        return redirect('login')

    group = get_object_or_404(
        ChatGroup,
        id=group_id
    )

    is_member = GroupMember.objects.filter(
        group=group,
        user=request.user
    ).exists()

    if not is_member:
        return redirect('messages')

    if request.method == 'POST':

        message_text = request.POST.get(
            'message',
            ''
        ).strip()

        if message_text:

            group_message = GroupMessage.objects.create(
                group=group,
                sender=request.user,
                message=message_text
            )

            members = GroupMember.objects.filter(
                group=group
            ).exclude(
                user=request.user
            ).select_related(
                'user'
            )

            for member in members:

                Notification.objects.create(
                    recipient=member.user,
                    sender=request.user,
                    notification_type='group_message',
                    message=(
                        f'New message in '
                        f'{group.name}'
                    ),
                    target_url=(
                        f'/messages/group/{group.id}/'
                    )
                )

        return redirect(
            'group_chat',
            group_id=group.id
        )

    group_messages = group.messages.select_related(
        'sender'
    ).order_by(
        'created_at'
    )

    unread_messages = group.messages.exclude(
        sender=request.user
    ).exclude(
        read_by__user=request.user
    )

    for message in unread_messages:

        GroupMessageRead.objects.get_or_create(
            message=message,
            user=request.user
        )

    members = GroupMember.objects.filter(
        group=group
    ).select_related(
        'user'
    )

    return render(
        request,
        'users/group_chat.html',
        {
            'group': group,
            'group_messages': group_messages,
            'members': members
        }
    )


def can_add_to_group(group, user):

    if group.add_permission == ChatGroup.ADD_EVERYONE:
        return True

    if group.add_permission == ChatGroup.ADD_FOLLOWERS:

        return Follow.objects.filter(
            follower=user,
            following=group.creator
        ).exists()

    if group.add_permission == ChatGroup.ADD_FOLLOWING:

        return Follow.objects.filter(
            follower=group.creator,
            following=user
        ).exists()

    return False


def add_group_member(request, group_id, username):

    if not request.user.is_authenticated:
        return redirect('login')

    group = get_object_or_404(
        ChatGroup,
        id=group_id
    )

    target_user = get_object_or_404(
        User,
        username=username
    )

    if not GroupMember.objects.filter(
        group=group,
        user=request.user
    ).exists():

        return redirect(
            'messages'
        )

    if GroupMember.objects.filter(
        group=group,
        user=target_user
    ).exists():

        return redirect(
            'group_chat',
            group_id=group.id
        )

    if not can_add_to_group(
        group,
        request.user
    ):

        return redirect(
            'group_chat',
            group_id=group.id
        )

    GroupMember.objects.create(
        group=group,
        user=target_user
    )

    Notification.objects.create(
        recipient=target_user,
        sender=request.user,
        notification_type='group_added',
        message=(
            f'@{request.user.username} '
            f'added you to {group.name}'
        ),
        target_url=(
            f'/messages/group/{group.id}/'
        )
    )

    return redirect(
        'group_chat',
        group_id=group.id
    )


# ============================================================
# AUTH
# ============================================================

def register(request):

    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                'users/register.html',
                {
                    'error': 'Username already exists.'
                }
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        UserProfile.objects.create(
            user=user
        )

        login(
            request,
            user
        )

        return redirect('profile')

    return render(
        request,
        'users/register.html'
    )


def user_login(request):

    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

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

            return redirect('profile')

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

    return redirect('login')