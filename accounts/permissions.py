from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            raise PermissionDenied(_('کاربر فعال نیست.'))

        if not request.user.has_perm('accounts.can_employee'):
            raise PermissionDenied(_('کاربر مجوزهای لازم را ندارد.'))

        # Common error message
        complete_profile_error = _('لطفاً پروفایل خود را به طور کامل پر کنید تا بتوانید ادامه دهید.')

        # Check User Profile
        user_profile = getattr(request.user, 'profiles', None)
        if user_profile is None or not all([
            user_profile.bio,
            user_profile.avatar,
            user_profile.age,
            user_profile.gender,
        ]):
            raise PermissionDenied(complete_profile_error)

        # Check Employee Profile
        employee_profile = getattr(user_profile, 'employee_profile', None)
        if employee_profile is None or not employee_profile.username:
            raise PermissionDenied(complete_profile_error)

        # Check for the existence of a social link
        if not employee_profile.social_links.exists():
            raise PermissionDenied(complete_profile_error)

        return True