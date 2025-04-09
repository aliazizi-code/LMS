from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            raise PermissionDenied('کاربر فعال نیست.')

        if not (request.user.has_perm('courses.can_teacher') and request.user.has_perm('accounts.can_employee')):
            raise PermissionDenied('کاربر مجوزهای لازم را ندارد.')

        return True