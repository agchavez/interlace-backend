

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
from ..exceptions import TokenInvalid, MissingCredentials
class AuthView(viewsets.GenericViewSet):
    serializer_class = UserSerializer

    @csrf_exempt
    @action(methods=['post'], detail=False)
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

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

    @action(methods=['post'], detail=False)
    def logout(self, request):
        logout(request)
        return Response({'success': 'Sesión cerrada correctamente'})

    @action(methods=['post'], detail=False, url_path='refresh-token')
    def refresh_token(self, request):
        refresh_token = request.data.get('refresh_token')

        if refresh_token is None:
            raise MissingCredentials({
                'mensage': 'refresh_token es requerido',
                'error_code': 'missing_refresh_token'
            })

        try:
            refresh_token = RefreshToken(refresh_token)
            access_token = str(refresh_token.access_token)
            access_token_obs = AccessToken(access_token)
            user_id = access_token_obs['user_id']

        except Exception as e:
            raise TokenInvalid({
                'mensage': 'refresh_token inválido',
                'error_code': 'invalid_refresh_token'
            })

        return Response({
            'user': UserSerializer(UserModel.objects.get(id=user_id)).data,
            'token': {
                'access': access_token,
                'refresh': str(refresh_token),
                'exp': access_token_obs['exp'],
            }
        })
