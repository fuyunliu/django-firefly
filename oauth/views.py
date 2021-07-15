from functools import partial

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework import mixins, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from commons import selectors
from commons.permissions import IsMeOrAdmin, IsOwnerOrAdmin
from oauth import logout_user
from oauth.email import DestroyUserEmail
from oauth.models import Profile
from oauth.serializers import (
    GroupSerializer,
    ProfileSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserDestroySerializer,
    PhoneCodeSerializer,
    EmailCodeSerializer,
    SetPhoneSerializer,
    SetEmailSerializer,
    SetUsernameSerializer,
    SetNicknameSerializer,
    SetPasswordSerializer,
    PhoneAndCodeSerializer,
    EmailAndCodeSerializer,
    PhoneAndPasswordSerializer,
    EmailAndPasswordSerializer,
    UsernameAndPasswordSerializer
)
from oauth.tasks import destroy_user

UserModel = get_user_model()


class TokenAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response('You are logged in.')

    def put(self, request, *args, **kwargs):
        token = request.auth
        token.set_exp()
        data = {'access': str(token)}
        return Response(data, status=status.HTTP_201_CREATED)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        logout_user(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        ctx = {'request': self.request, 'format': self.format_kwarg, 'view': self}
        kwargs.setdefault('context', ctx)
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        data = self.request.data
        if self.request.method == 'POST':
            if 'phone_code' in data:
                if 'phone' in data:
                    return PhoneAndCodeSerializer
                elif 'email' in data:
                    return EmailAndCodeSerializer
            elif 'password' in data:
                if 'username' in data:
                    return UsernameAndPasswordSerializer
                elif 'email' in data:
                    return EmailAndPasswordSerializer
                elif 'phone' in data:
                    return PhoneAndPasswordSerializer
            else:
                return PhoneAndCodeSerializer
        return PhoneAndCodeSerializer


class PhoneCodeView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        ctx = {'request': self.request, 'format': self.format_kwarg, 'view': self}
        kwargs.setdefault('context', ctx)
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        data = self.request.data
        if self.request.method == 'POST':
            if 'phone' in data:
                return PhoneCodeSerializer
            elif 'email' in data:
                return EmailCodeSerializer
            else:
                return PhoneCodeSerializer
        return PhoneCodeSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsMeOrAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if self.action == 'list':
            if not user.is_staff:
                queryset = queryset.filter(pk=user.pk)
            queryset = selectors.select_user(queryset, self.request)
        elif self.action == 'retrieve':
            queryset = selectors.select_user(queryset, self.request)

        return queryset

    def get_instance(self):
        return self.request.user

    def get_permissions(self):
        action_perms = {
            'create': [IsAdminUser],
            'activation': [IsAdminUser]
        }
        self.permission_classes = action_perms.get(self.action, self.permission_classes)
        return super().get_permissions()

    def get_serializer_class(self):
        UserFollowSerializer = partial(UserSerializer, expand=['is_following', 'is_followed'])
        action_seres = {
            'list': UserFollowSerializer,
            'retrieve': UserFollowSerializer,
            'create': UserCreateSerializer,
            'destroy': UserDestroySerializer,
            'set_email': SetEmailSerializer,
            'set_phone': SetPhoneSerializer,
            'set_username': SetUsernameSerializer,
            'set_nickname': SetNicknameSerializer,
            'set_password': SetPasswordSerializer
        }
        return action_seres.get(self.action, self.serializer_class)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_destroy(user)
        DestroyUserEmail(request).send([user.email])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        destroy_user.apply_async((instance.pk,), eta=timezone.now() + settings.DESTROY_USER_TIMEDELTA, expires=60)

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['post'], detail=True)
    def activation(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='set-username')
    def set_username(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        user.set_username(username)
        user.save(update_fields=['username'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='set-nickname')
    def set_nickname(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        nickname = serializer.validated_data['nickname']
        profile = user.profile
        profile.set_nickname(nickname)
        profile.save(update_fields=['nickname'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='set-password')
    def set_password(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        user.set_password(password)
        user.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='set-email')
    def set_email(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = self.get_object()
        user.email = email
        user.save(update_fields=['email'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='set-phone')
    def set_phone(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        user = self.get_object()
        user.phone = phone
        user.save(update_fields=['phone'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=True)
    def profile(self, request, *args, **kwargs):
        user = self.get_object()
        user.profile.viewed()
        return Response(ProfileSerializer(user.profile).data)

    @action(methods=['get'], detail=True)
    def articles(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_articles(self, user, request)

    @action(methods=['get'], detail=True)
    def pins(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_pins(self, user, request)

    @action(methods=['get'], detail=True)
    def tags(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_tags(self, user, request)

    @action(methods=['get'], detail=True)
    def questions(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_questions(self, user, request)

    @action(methods=['get'], detail=True)
    def comments(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_comments(self, user, request)

    @action(methods=['get'], detail=True)
    def collections(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_collections(self, user, request)

    @action(methods=['get'], detail=True)
    def following(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_following(self, user, request)

    @action(methods=['get'], detail=True)
    def followers(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_followers(self, user, request)

    @action(methods=['get'], detail=True, url_path='liking-collections')
    def liking_collections(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_liking_collections(self, user, request)

    @action(methods=['get'], detail=True, url_path='following-collections')
    def following_collections(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_following_collections(self, user, request)

    @action(methods=['get'], detail=True, url_path='liking-comments')
    def liking_comments(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_liking_comments(self, user, request)

    @action(methods=['get'], detail=True, url_path='liking-articles')
    def liking_articles(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_liking_articles(self, user, request)

    @action(methods=['get'], detail=True, url_path='liking-pins')
    def liking_pins(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_liking_pins(self, user, request)

    @action(methods=['get'], detail=True, url_path='following-categories')
    def following_categories(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_following_categories(self, user, request)

    @action(methods=['get'], detail=True, url_path='following-topics')
    def following_topics(self, request, *args, **kwargs):
        user = self.get_object()
        return selectors.user_following_topics(self, user, request)


class ProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Profile.objects.all().select_related('user')
    serializer_class = ProfileSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if self.action == 'list' and not user.is_staff:
            queryset = queryset.filter(pk=user.pk)
        return queryset

    def get_instance(self):
        user = self.request.user
        profile = user.profile
        return profile

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        profile.viewed()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]
