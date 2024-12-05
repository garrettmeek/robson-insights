from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.signing import Signer
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException

from robson_insight import settings
from .serializers import *
from .models import UserProfile, Group, Invite
from .permissions import IsInGroup, IsGroupAdmin

class UserProfileListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return UserProfile.objects.all()

class UserProfileDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        queryset = UserProfile.objects.filter(pk=pk)
        return queryset

class GroupListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(userprofile__user=self.request.user)

    def perform_create(self, serializer):
        group = serializer.save()

        UserProfile.objects.create(
            user=self.request.user,
            group=group,
            is_admin=True
        )

class CreateGroup(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group_name = request.data.get('group_name', '').strip()
        if not group_name:
            return Response({'error': 'Group name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if len(group_name) > 100:
            return Response({'error': 'Group name cannot exceed 100 characters'}, status=status.HTTP_400_BAD_REQUEST)
        if len(group_name) < 5:
            return Response({'error': 'Group name must be at least 5 characters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if Group.objects.filter(name__iexact=group_name).exists():
                return Response({'error': 'A group with this name already exists'}, status=status.HTTP_400_BAD_REQUEST)

            group = Group.objects.create(name=group_name)
            UserProfile.objects.create(user=request.user, group=group, is_admin=True)

            return Response(
                {'success': f'Group "{group.name}" created. You are now an administrator of this group.'},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print('Error:', str(e))
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsGroupAdmin]
    serializer_class = GroupSerializer

    def get_queryset(self):
        pk = self.kwargs.get('group_pk')
        queryset = Group.objects.filter(pk=pk)
        return queryset
    
class GroupUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer
    queryset = Group.objects.all()

    def get_object(self):
        group_pk = self.kwargs.get('group_pk')
        return Group.objects.get(pk=group_pk)

class UserProfileInGroupListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsInGroup]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        group_pk = self.kwargs.get('group_pk')
        queryset = UserProfile.objects.filter(group=group_pk)
        return queryset
    

class AddUserToGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.data.get('username', '').lower()
        group_id = request.data.get('group_id')

        if not username or not group_id:
            return Response({'error': 'Username and group_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username__iexact=username)
            group = Group.objects.get(id=group_id)

            requesting_user_admin = UserProfile.objects.get(user=request.user, group=group).is_admin
            if not requesting_user_admin:
                return Response({'error': 'You are not authorized to add users to this group.'}, status=status.HTTP_403_FORBIDDEN)

            user_profile, created = UserProfile.objects.get_or_create(user=user, group=group)
            if created:
                return Response({'success': f'User {user.username} was added to group {group.name}'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': f'User {user.username} is already in group {group.name}'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'error': 'An error occurred while adding the user to the group.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RemoveUserFromGroup(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.data.get('username')
        group_id = request.data.get('group_id')

        if not username or not group_id:
            return Response({'error': 'Username and group_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
            group = Group.objects.get(id=group_id)
            user_profile = UserProfile.objects.get(user=user, group=group)
            num_user_profiles = UserProfile.objects.filter(user=request.user).count()

            requesting_user_admin = UserProfile.objects.get(user=request.user, group=group).is_admin
            if not requesting_user_admin:
                return Response({'error': 'You are not authorized to remove users from this group.'}, status=status.HTTP_403_FORBIDDEN)
            
            if num_user_profiles <= 1:
                return Response({'error': 'You must be a member of at least one group.'}, status=status.HTTP_403_FORBIDDEN)

            user_profile.delete()

            return Response({'success': f'User {username} removed from group {group.name}'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User is not in this group'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LeaveGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group_id = request.data.get('group_id')

        if not group_id:
            return Response(
                {'error': 'Group ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            group = Group.objects.get(id=group_id)
            user_profile = UserProfile.objects.get(
                user=request.user, 
                group=group
            )

            # Prevent the last admin from leaving
            admin_count = UserProfile.objects.filter(
                group=group, 
                is_admin=True
            ).count()
            
            if user_profile.is_admin and admin_count <= 1:
                return Response(
                    {'error': 'Cannot leave group: you are the last administrator'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_profile.delete()

            return Response(
                {'success': f'You have left the group {group.name}'}, 
                status=status.HTTP_200_OK
            )

        except Group.DoesNotExist:
            return Response(
                {'error': 'Group not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this group'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
               
class GetInviteView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            invite = Invite.objects.get(token=token)
            return Response({
                "email": invite.email,
                "group": invite.group.name
            }, status=status.HTTP_200_OK)
        except Invite.DoesNotExist:
            return Response({"error": "Invite not found."}, status=status.HTTP_404_NOT_FOUND)
             
             
class ChangeGroupAdminView(APIView):
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    def post(self, request, group_pk):
        new_admin_username = request.data.get('username')

        if not new_admin_username:
            return Response(
                {'error': 'New admin username is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            group = Group.objects.get(pk=group_pk)
            new_admin_user = User.objects.get(username__iexact=new_admin_username)
            new_admin_profile = UserProfile.objects.get(user=new_admin_user, group=group)
        except Group.DoesNotExist:
            return Response(
                {'error': 'Group not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User is not a member of the group.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        current_admin_profile = UserProfile.objects.get(user=request.user, group=group, is_admin=True)

        if current_admin_profile.user != request.user:
            return Response(
                {'error': 'You are not authorized to change the admin of this group.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            with transaction.atomic():
                current_admin_profile.is_admin = False
                current_admin_profile.save()

                new_admin_profile.is_admin = True
                new_admin_profile.save()
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {'success': f'User {new_admin_user.username} is now the admin of group {group.name}.'},
            status=status.HTTP_200_OK        )
        
class InviteCreateView(generics.CreateAPIView):
    serializer_class = SmallInviteSerializer
    permission_classes = [permissions.IsAuthenticated, IsGroupAdmin]

    def perform_create(self, serializer):
        group = Group.objects.get(pk=self.kwargs['group_pk'])
        email = serializer.validated_data['email']
        signer = Signer()
        token = signer.sign(email)
        token = token.split(':')[1]
        invite = serializer.save(token=token, group=group, email=email)
        
        invite_url = f"http://localhost:8081/signup?token={token}"
        
        if not User.objects.filter(email=email).exists():
            subject = 'Robson Insights Invitation'
            context = {'invite_url': invite_url}
            html_content = render_to_string('email_invite.html', context)
        else:
            subject = 'Robson Insights Invitation'
            context = {'invite_url': invite_url}
            html_content = render_to_string('email_invite.html', context)

        try:
            # Set up the email with HTML content
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=invite_url,  # Fallback text for email clients that don't support HTML
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send(fail_silently=False)
        except Exception as e:
            # If email sending fails, delete the created invite and re-raise the exception
            invite.delete()
            raise APIException(f"Failed to send invitation email: {str(e)}")
        
        
class MassInviteCreateView(APIView):
    serializer_class = MassInviteSerializer
    permission_classes = [IsAuthenticated, IsGroupAdmin]

    def post(self, request, *args, **kwargs):
        group_pk = kwargs.get('group_pk')
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            emails = serializer.validated_data['emails']
            group = Group.objects.get(pk=group_pk)
            signer = Signer()
            created_invites = []

            try:
                for email in emails:
                    token = signer.sign(email).split(':')[1]
                    invite = Invite.objects.create(token=token, group=group, email=email)
                    created_invites.append(invite)
                    
                    invite_url = f"http://localhost:8081/signup?token={token}"
                    subject = 'Robson Insights Invitation'
                    context = {'invite_url': invite_url}
                    html_content = render_to_string('email_invite.html', context)
                    
                    # Use EmailMultiAlternatives to send HTML email
                    email_msg = EmailMultiAlternatives(
                        subject=subject,
                        body=invite_url,  # Fallback text for email clients that don’t support HTML
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[email],
                    )
                    email_msg.attach_alternative(html_content, "text/html")
                    email_msg.send(fail_silently=False)
                
                return Response(
                    {'success': f'Invitations sent to {len(emails)} users.'},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                # Roll back invites if an error occurs
                for invite in created_invites:
                    invite.delete()
                return Response(
                    {'error': f"Failed to send invitation emails: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
        
class AcceptInviteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, token):
        try:
            invite = Invite.objects.get(token=token)
        except Invite.DoesNotExist:
            return Response(
                {"error": "Invite not found."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if (invite.is_expired()):
            invite.delete()
            return Response(
            {"error": "This invite has expired."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
        UserProfile.objects.create(
            user=request.user,
            group=invite.group,
            is_admin=False
        )
        
        invite.delete()
        
        return Response(
            {"message": "You have successfully joined the group."},
            status=status.HTTP_200_OK
        ) 
      
class RejectInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, token):
        try:
            invite = Invite.objects.get(token=token, email=request.user.email)
            invite.delete()
            return Response({"message": "Invitation rejected successfully."}, status=status.HTTP_200_OK)
        except Invite.DoesNotExist:
            return Response({"error": "Invite not found."}, status=status.HTTP_404_NOT_FOUND)
              
class TogglePermissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.data.get('username')
        group_id = request.data.get('group_id')
        toggle_view = request.data.get('toggle_view', False)

        try:
            group = Group.objects.get(id=group_id)
            current_admin_profile = UserProfile.objects.get(user=request.user,group=group)
            if not current_admin_profile.is_admin:
                return Response({"error": "You are not authorized to toggle permissions."}, status=status.HTTP_403_FORBIDDEN)

            target_user = User.objects.get(username=username)
            target_user_profile = UserProfile.objects.get(user=target_user, group=group)

            target_user_profile.can_view = toggle_view

            target_user_profile.save()

            return Response({"success": f"Permissions updated for {target_user.username}."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found in this group."}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Group not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InviteListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InviteSerializer
    
    def get_queryset(self):
        user = self.request.user
        return Invite.objects.filter(email=user)
        
class UserGroupsCanView(generics.ListAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_profile = UserProfile.objects.filter(user=user, can_view=True)
        
        if user_profile.exists():
            return Group.objects.filter(userprofile__in=user_profile)
        return Group.objects.none()
