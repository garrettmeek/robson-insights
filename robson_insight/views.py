from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken, APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import UserRegistrationSerializer
from users.models import Invite, UserProfile, User


class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "token": token.key,
            },
            status=status.HTTP_200_OK
        )
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Logout successful'})
 
class RegisterView(APIView):
    serializer_class = UserRegistrationSerializer
    
    def post(self, request, token):
        try:
                invite = Invite.objects.get(token=token)
                if invite.is_expired():
                    invite.delete()
                    return Response(
                        {"error": "This invite has expired."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                user, created = User.objects.get_or_create(
                    email=serializer.validated_data['email'],
                    defaults={
                        'username': serializer.validated_data['email'],
                        'first_name': serializer.validated_data['first_name'],
                        'last_name': serializer.validated_data['last_name'],
                        'password': serializer.validated_data['password']
                    }
                )
                
                if not created:
                    if UserProfile.objects.filter(user=user, group=invite.group).exists():
                        return Response(
                            {"error": "User is already a member of this group."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                UserProfile.objects.create(user=user, group=invite.group)
                
                invite.delete()
                
                token, created = Token.objects.get_or_create(user=user)
                
                return Response(
                    {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "token": token.key,
                    },
                    status=status.HTTP_201_CREATED
                )
                
        except Invite.DoesNotExist:
            return Response(
                {"error": "Invite not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )