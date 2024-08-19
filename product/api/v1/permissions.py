from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.models import Subscription


def make_payment(request):
    # TODO
    pass


class IsStudentOrIsAdmin(BasePermission):
    message = 'У Вас нет доступа к материалам запрашиваемого курса'

    def has_permission(self, request, view):
        course_id = int(request.parser_context.get('kwargs').get('course_id'))
        return (
            request.user.is_staff
            or (
                request.user.is_authenticated
                and course_id
                in request.user.courses.values_list('id', flat=True)
            )
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_staff
            or (
                request.user in obj.course.users
                and request.method in SAFE_METHODS
            )
        )


class ReadOnlyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.method in SAFE_METHODS
