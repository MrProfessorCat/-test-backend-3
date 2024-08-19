from django.db.models import Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_list_or_404
from django.utils import timezone

from courses.models import Group
from users.models import Subscription


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """
    Распределение нового студента в группу курса.

    """

    if created:
        group_with_min_users = get_list_or_404(
            Group.objects.filter(
                Q(course=instance.course)
            ).annotate(
                users_num=Count('users')
            ).order_by('users_num')
        )[0]
        group_with_min_users.users.add(instance.user)
