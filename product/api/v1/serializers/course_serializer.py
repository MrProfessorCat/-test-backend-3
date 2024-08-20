from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.db.models.functions import Round
from rest_framework import serializers

from courses.models import Course, Group, Lesson
from users.models import Subscription

from .user_serializer import UserSerializer

User = get_user_model()


class LessonSerializer(serializers.ModelSerializer):
    """Список уроков."""

    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Lesson
        fields = (
            'title',
            'link',
            'course'
        )


class CreateLessonSerializer(serializers.ModelSerializer):
    """Создание уроков."""

    class Meta:
        model = Lesson
        fields = (
            'title',
            'link',
            'course'
        )


class StudentSerializer(serializers.ModelSerializer):
    """Студенты курса."""

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )


class GroupSerializer(serializers.ModelSerializer):
    """Список групп."""

    # TODO Доп. задание

    class Meta:
        model = Group
        fields = (
            'title',
            'course',
        )


class CreateGroupSerializer(serializers.ModelSerializer):
    """Создание групп."""

    class Meta:
        model = Group
        fields = (
            'title',
            'course',
        )


class MiniLessonSerializer(serializers.ModelSerializer):
    """Список названий уроков для списка курсов."""

    class Meta:
        model = Lesson
        fields = (
            'title',
        )


class CourseSerializer(serializers.ModelSerializer):
    """Список курсов."""

    lessons = MiniLessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField(read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    groups_filled_percent = serializers.SerializerMethodField(read_only=True)
    demand_course_percent = serializers.SerializerMethodField(read_only=True)

    def get_lessons_count(self, obj):
        """Количество уроков в курсе."""
        return Lesson.objects.filter(course=obj).count()

    def get_students_count(self, obj):
        """Общее количество студентов на курсе."""
        return User.objects.filter(courses=obj).count()

    def get_groups_filled_percent(self, obj):
        """Процент заполнения групп, если в группе максимум 30 чел.."""
        res = Group.objects.filter(course=obj).annotate(
            fill_percent=Round(
                Count('users') * 100 / settings.MAX_USERS_IN_GROUP
            )
        ).aggregate(
            avg_percent=Round(Avg('fill_percent'))
        ).get('avg_percent')
        return res

    def get_demand_course_percent(self, obj):
        """Процент приобретения курса."""
        return (
            round(
                100 / User.objects.count()
                * Subscription.objects.filter(course=obj).count()
            )
        )

    class Meta:
        model = Course
        fields = (
            'id',
            'author',
            'title',
            'start_date',
            'price',
            'lessons_count',
            'lessons',
            'demand_course_percent',
            'students_count',
            'groups_filled_percent',
        )


class CourseShortInfoSerialize(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField(read_only=True)

    def get_lessons_count(self, obj):
        """Количество уроков в курсе."""
        return Lesson.objects.filter(course=obj).count()

    class Meta:
        model = Course
        fields = (
            'author',
            'title',
            'start_date',
            'price',
            'lessons_count'
        )


class CreateCourseSerializer(serializers.ModelSerializer):
    """Создание курсов."""

    class Meta:
        model = Course
        fields = '__all__'


class PaidCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            'author',
            'title',
            'start_date',
            'price',
            'users'
        )
