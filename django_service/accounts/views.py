from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    # Public endpoint: no token needed, so no padlock in Swagger
    authentication_classes = []
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
        except (KeyError, TokenError):
            return Response({"detail": "Invalid or missing refresh token."},
                            status=status.HTTP_400_BAD_REQUEST)
        # A user can only blacklist their own refresh token
        if str(token.get("user_id")) != str(request.user.pk):
            return Response({"detail": "Invalid or missing refresh token."},
                            status=status.HTTP_400_BAD_REQUEST)
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user