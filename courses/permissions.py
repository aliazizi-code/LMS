from rest_framework.exceptions import PermissionDenied

from accounts.permissions import IsEmployee

class IsTeacher(IsEmployee):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        
        if not request.user.has_perm('courses.can_teacher'):
            raise PermissionDenied('کاربر مجوزهای لازم را ندارد.')

        return True