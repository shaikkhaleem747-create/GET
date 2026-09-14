from django.db.models import Count
from .models import Message, Notification


def notification_count(request):

    unread_notification_count = 0
    unread_message_people_count = 0

    if request.user.is_authenticated:

        unread_notification_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        unread_message_people_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).values(
            'sender'
        ).distinct().count()

    return {
        'unread_notification_count': (
            unread_notification_count
        ),
        'unread_message_people_count': (
            unread_message_people_count
        )
    }