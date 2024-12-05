from rest_framework import permissions
from .models import UserProfile

class IsInGroup(permissions.BasePermission):

    def has_permission(self, request, view):
        group_pk = view.kwargs.get('group_pk')
        return UserProfile.objects.filter(user=request.user, group_id=group_pk).exists()
    
    
class IsGroupAdmin(permissions.BasePermission):
    
    def has_permission(self, request, view):
        group_pk = view.kwargs.get('group_pk')
        
        try:
            UserProfile.objects.get(user=request.user, group_id=group_pk, is_admin=True)
        except UserProfile.DoesNotExist:
            return False
        
        return True
