from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from accounts.models import EmployeeProfile

class IsEmployee(IsAuthenticated):
    def has_permission(self, request, view):
        super().has_permission(request, view)

        if not request.user.is_active:
            raise PermissionDenied(_('کاربر فعال نیست.'))

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
    
   
class IsEmployeeForProfile(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        super().has_permission(request, view)
        
        if not request.user.has_perm('accounts.can_employee'):
            raise PermissionDenied(_('کاربر مجوزهای لازم را ندارد.'))
        
        if not request.user.is_active:
            raise PermissionDenied(_('کاربر فعال نیست.'))
        
        return True
    

class IsAnonymous(IsAuthenticated):
    def has_permission(self, request, view):
        return not super().has_permission(request, view)
    