from rest_framework import permissions
from .models import Entry
from users.models import UserProfile


class CanReadEntry(permissions.BasePermission):

    def has_permission(self, request, view):
        
        pk = view.kwargs.get('pk')
        
        try:
            entry = Entry.objects.get(pk=pk)
            user_profile = UserProfile.objects.get(user=request.user, group=entry.group)
            return user_profile.can_view | user_profile.is_admin
        except Entry.DoesNotExist:
            return False
        except UserProfile.DoesNotExist:
            return False