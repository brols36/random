from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import logout, authenticate
from .serializers import UserSerializer, DepositSerializer, WithdrawSerializer
from .models import CustomUser

class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not username and not email:
            return Response({'error': 'Username or email is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        if username:
            try:
                user = CustomUser.objects.get(username=username)
                if user.check_password(password):
                    user = authenticate(username=username, password=password)
            except CustomUser.DoesNotExist:
                user = None

        if email and not user:
            try:
                user = CustomUser.objects.get(email=email)
                if user.check_password(password):
                    user = authenticate(username=user.username, password=password)
            except CustomUser.DoesNotExist:
                user = None

        if user and user.is_authenticated:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        if request.auth:
            request.auth.delete()  # Deletes the token associated with the current user
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

class DepositView(generics.GenericAPIView):
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            request.user.deposit(amount)
            return Response({'message': 'Deposit successful', 'new_balance': request.user.security_deposit}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WithdrawView(generics.GenericAPIView):
    serializer_class = WithdrawSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            if request.user.withdraw(amount):
                return Response({'message': 'Withdrawal successful', 'new_balance': request.user.security_deposit}, status=status.HTTP_200_OK)
            return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
