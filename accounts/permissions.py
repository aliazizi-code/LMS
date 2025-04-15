from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from accounts.models import EmployeeProfile

class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        super().has_permission(request, view)

        if not request.user.has_perm('accounts.can_employee'):
            raise PermissionDenied(_('کاربر مجوزهای لازم را ندارد.'))

        # Check Completed Profiles
        try:
            employee_profile = EmployeeProfile.objects.filter_completed_profiles().get(
                user_profile__user=request.user
            )
                
        except EmployeeProfile.DoesNotExist:
            raise PermissionDenied(_('لطفاً پروفایل خود را به طور کامل پر کنید تا بتوانید ادامه دهید.'))

        return True
    
   
class IsEmployeeForProfile(BasePermission):
    def has_object_permission(self, request, view, obj):
        super().has_permission(request, view)
        
        if not request.user.has_perm('accounts.can_employee'):
            raise PermissionDenied(_('کاربر مجوزهای لازم را ندارد.'))
        
        return True


# TODO : Bro 00
class IsAnonymousUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        super().has_permission(request, view)
        # ...
        return True
