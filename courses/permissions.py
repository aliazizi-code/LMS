from rest_framework.permissions import BasePermission


class CanTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('courses.can_teacher')
