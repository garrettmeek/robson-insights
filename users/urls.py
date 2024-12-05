from django.urls import path
from .views import *


app_name = 'users'

urlpatterns = [
    path('', UserProfileListView.as_view()),
    path('<int:pk>/', UserProfileDetailView.as_view()),
    path('groups/', GroupListCreateView.as_view()),
    path('groups/<int:group_pk>/', GroupDetailView.as_view()),
    path('groups/<int:group_pk>/update/', GroupUpdateView.as_view(), name='update-group'),
    path('get-groups-users/<int:group_pk>/', UserProfileInGroupListView.as_view()),
    path('add-user-to-group/', AddUserToGroupView.as_view(), name='add-user-to-group'),
    path('remove-user-from-group/', RemoveUserFromGroup.as_view(), name='remove-user-from-group'),
    path('leave-group/', LeaveGroupView.as_view(), name='leave-group'),
    path('create-group/', CreateGroup.as_view(), name = 'create-group'),
    path('groups/<int:pk>/change-admin/', ChangeGroupAdminView.as_view(), name='change-group-admin'),
    path('toggle-permissions/', TogglePermissionsView.as_view(), name='toggle-permissions'),
    path('groups-can-view/', UserGroupsCanView.as_view(), name="groups-can-view"),

    ## Invitations
    path('invitations/', InviteListView.as_view(), name='invite-list'),
    path('create-invitation/<int:group_pk>/', InviteCreateView.as_view(), name='create-invite'),
    path('mass-invite/<int:group_pk>/', MassInviteCreateView.as_view()),
    path('accept-invitation/<str:token>/', AcceptInviteView.as_view(), name='accept-invite'),
    path('reject-invitation/<str:token>/', RejectInviteView.as_view(), name='reject-invite'),
    path('get-invitation/<str:token>/', GetInviteView.as_view(), name='get-invite'),
]