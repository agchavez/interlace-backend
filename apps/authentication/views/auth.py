

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import  Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import update_last_login
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

#Local
from ..serializers import LoginSerializer
from apps.user.serializers import UserSerializer
from apps.user.models import UserModel
class AuthView(viewsets.GenericViewSet):
    serializer_class = UserSerializer

    @csrf_exempt
    @action(methods=['post'], detail=False)
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        if user is not None:
            update_last_login(None, user)
            # el token durará 24 horas
            refresh = RefreshToken.for_user(user)
            access_token_obs = AccessToken(str(refresh.access_token))
            return Response({
                'user': UserSerializer(user).data,
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'exp': access_token_obs['exp'],
                }
            })
        else:
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)

    @action(methods=['post'], detail=False)
    def logout(self, request):
        logout(request)
        return Response({'success': 'Sesión cerrada correctamente'})

    @action(methods=['post'], detail=False, url_path='refresh-token')
    def refresh_token(self, request):
        refresh_token = request.data.get('refresh_token')
        if refresh_token is None:
            return Response({'error': 'refresh_token es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh_token = RefreshToken(refresh_token)
            access_token = str(refresh_token.access_token)
            access_token_obs = AccessToken(access_token)
            user_id = access_token_obs['user_id']

        except Exception as e:
            return Response({'error': 'refresh_token inválido'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'user': UserSerializer(UserModel.objects.get(id=user_id)).data,
            'token': {
                        'access': access_token,
                        'refresh': str(refresh_token),
                        'exp': access_token_obs['exp'],
            }
                        })
