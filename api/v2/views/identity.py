from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework import status

from core.models import Identity, Group

from api.v2.serializers.details import IdentitySerializer
from api.v2.views.base import AuthModelViewSet
from api.v2.views.mixins import MultipleFieldLookup


class IdentityViewSet(MultipleFieldLookup, AuthModelViewSet):

    """
    API endpoint that allows providers to be viewed or edited.
    """
    lookup_fields = ("id", "uuid")
    serializer_class = IdentitySerializer
    queryset = Identity.objects.all()
    http_method_names = ['get', 'head', 'options', 'trace']

    @detail_route(methods=['GET'])
    def export(self, request, pk=None):
        """
        Until a better method comes about, we will handle InstanceActions here.
        """
        if type(pk) == int:
            kwargs = {"id": pk}
        else:
            kwargs = {"uuid": pk}
        identity = Identity.objects.get(**kwargs)
        export_data = identity.export()
        return Response(
            export_data,
            status=status.HTTP_200_OK)

    def queryset_by_username(self, username):
        try:
            group = Group.objects.get(name=username)
        except Group.DoesNotExist:
            return Identity.objects.none()
        identities = group.current_identities.all()
        return identities

    def get_queryset(self):
        """
        Filter identities by current user
        """
        user = self.request.user
        if user.is_admin():
            if 'all_users' in self.request.GET:
                return Identity.objects.all()
            if 'username' in self.request.GET:
                target_username = self.request.GET.get('username')
                return self.queryset_by_username(target_username)
        return self.queryset_by_username(user.username)
