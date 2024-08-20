from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from djoser.serializers import UserSerializer
from rest_framework import serializers

from courses.models import Group
from users.models import Subscription

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователей."""

    class Meta:
        model = User
        fields = '__all__'


class StudentSerializer(UserSerializer):
    """Сериализатор с упрощенной информацией о пользователе"""

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email'
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""
    user = serializers.ReadOnlyField(source='user.id')
    course = serializers.ReadOnlyField(source='course.id')

    class Meta:
        model = Subscription
        fields = (
            'user',
            'course'
        )

    def validate(self, attrs):
        request = self.context.get('request')
        course = self.context.get('course')

        # Проверяем, не приобрел ли пользователь курс ранее
        if course in request.user.courses.all():
            raise serializers.ValidationError(
                (
                    f'Пользователь {request.user.username} '
                    f'уже приобрел курс «{course.title}».'
                )
            )

        # Проверяем, хватает ли у пользователя бонусов на покупку курса
        if course.price > request.user.balance.bonuses_amount:
            raise serializers.ValidationError(
                (
                    f'У пользователя {request.user.username} '
                    'недостаточно средств на покупку курса.'
                )
            )

        # Проверяем, есть ли места в группах
        # Лимиты: в одной группе не более 30 человек
        available_groups = Group.objects.filter(
            Q(course=course)
        ).annotate(
            users_num=Count('users')
        ).filter(
            Q(users_num__lt=settings.MAX_USERS_IN_GROUP)
        ).exists()
        if not available_groups:
            raise serializers.ValidationError(
                f'Все группы на курс «{course.title}» заполнены.'
            )
        return attrs
