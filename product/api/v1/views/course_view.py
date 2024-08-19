from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CourseShortInfoSerialize,
                                                  CreateCourseSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer,
                                                  PaidCourseSerializer)
from api.v1.serializers.user_serializer import SubscriptionSerializer
from courses.models import Course, Group
from users.models import Subscription


class LessonViewSet(viewsets.ModelViewSet):
    """Уроки."""

    permission_classes = (IsStudentOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.lessons.all()


class GroupViewSet(viewsets.ModelViewSet):
    """Группы."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.groups.all()


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin, )

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def pay(self, request, pk):
        """Покупка доступа к курсу (подписка на курс)."""

        course = get_object_or_404(Course.objects.select_related(), id=pk)
        serializer = PaidCourseSerializer(course)
        # Проверяем, не приобрел ли пользователь курс ранее
        if course in request.user.courses.all():
            return HttpResponseBadRequest(
                (
                    f'Пользователь {request.user.username} '
                    f'уже приобрел курс «{course.title}».'
                )
            )
        # Проверяем, хватает ли у пользователя бонусов на покупку курса
        if course.price > request.user.balance.bonuses_amount:
            return HttpResponseBadRequest(
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
            return HttpResponseBadRequest(
                f'Все группы на курс «{course.title}» заполнены.'
            )

        # Подписываем пользователя на курс и списываем
        # с его баланса стоимость курса
        with transaction.atomic():
            Subscription.objects.create(
                user=request.user, course=course
            )
            request.user.balance.bonuses_amount -= course.price
            request.user.balance.save()

        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(
        methods=('get',),
        detail=False,
        url_path='my_available',
        url_name='my_available',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_my_available_courses(self, request):
        """Метод позволяет получить список продуктов, доступных для покупки
        (курсы еще не куплены пользователем и у них есть флаг доступности)
        """
        queryset = Course.objects.all().filter(
            available=True).exclude(users=request.user)
        serializer = CourseShortInfoSerialize(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
