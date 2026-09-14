from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    full_name = models.CharField(
        max_length=100,
        blank=True
    )

    bio = models.TextField(
        max_length=500,
        blank=True
    )

    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username


class FriendRequest(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_friend_requests'
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_friend_requests'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    accepted = models.BooleanField(
        default=False
    )

    def __str__(self):
        return (
            f'{self.sender.username} → '
            f'{self.receiver.username}'
        )


class Follow(models.Model):

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'follower',
                    'following'
                ],
                name='unique_follow'
            )
        ]

    def __str__(self):
        return (
            f'{self.follower.username} '
            f'follows '
            f'{self.following.username}'
        )


class Notification(models.Model):

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications'
    )

    notification_type = models.CharField(
        max_length=50
    )

    message = models.CharField(
        max_length=255
    )

    friend_request = models.ForeignKey(
        FriendRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )

    target_url = models.CharField(
        max_length=500,
        blank=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f'{self.recipient.username} - '
            f'{self.message}'
        )


class Message(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )

    message = models.TextField(
        max_length=2000
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_read = models.BooleanField(
        default=False
    )

    def __str__(self):
        return (
            f'{self.sender.username} → '
            f'{self.receiver.username}'
        )


class ChatGroup(models.Model):

    ADD_EVERYONE = 'everyone'
    ADD_FOLLOWERS = 'followers'
    ADD_FOLLOWING = 'following'

    ADD_PERMISSION_CHOICES = [
        (
            ADD_EVERYONE,
            'Everyone'
        ),
        (
            ADD_FOLLOWERS,
            'Followers'
        ),
        (
            ADD_FOLLOWING,
            'Following'
        ),
    ]

    name = models.CharField(
        max_length=100
    )

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_chat_groups'
    )

    add_permission = models.CharField(
        max_length=20,
        choices=ADD_PERMISSION_CHOICES,
        default=ADD_EVERYONE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class GroupMember(models.Model):

    group = models.ForeignKey(
        ChatGroup,
        on_delete=models.CASCADE,
        related_name='members'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_group_memberships'
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'group',
                    'user'
                ],
                name='unique_group_member'
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.group.name}'
        )


class GroupMessage(models.Model):

    group = models.ForeignKey(
        ChatGroup,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_group_messages'
    )

    message = models.TextField(
        max_length=2000
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f'{self.sender.username} - '
            f'{self.group.name}'
        )


class GroupMessageRead(models.Model):

    message = models.ForeignKey(
        GroupMessage,
        on_delete=models.CASCADE,
        related_name='read_by'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='read_group_messages'
    )

    read_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'message',
                    'user'
                ],
                name='unique_group_message_read'
            )
        ]