from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework import status

from core.models import Identity, Group, Quota

from api.v2.serializers.details import IdentitySerializer
from api.v2.views.base import AuthModelViewSet
from api.v2.views.mixins import MultipleFieldLookup
from service.tasks import admin as admin_task


class IdentityViewSet(MultipleFieldLookup, AuthModelViewSet):

    """
    API endpoint that allows providers to be viewed or edited.
    """
    lookup_fields = ("id", "uuid")
    serializer_class = IdentitySerializer
    queryset = Identity.objects.all()
    http_method_names = ['get', 'head', 'options', 'trace', 'patch']

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

    def update(self, request, pk=None, partial=False):
        if not request.user.is_admin():
            return Response("Insufficient privileges", status=status.HTTP_403_FORBIDDEN)

        if not pk:
            return Response("Missing identity primary key",
                            status=status.HTTP_400_BAD_REQUEST)

        identity = Identity.objects.get(uuid=pk)
        serializer = self.get_serializer_class()

        data = request.data
        if 'quota' in data and 'id' in data.get('quota'):
            quota_id = data.get('quota').get('id')
            identity.quota = Quota.objects.get(id=quota_id)
            identity.save()
            admin_task.set_provider_quota.delay(str(identity.uuid))

        serialized = serializer(identity,
                                context={'request': self.request})

        return Response(
                serialized.data,
                status=status.HTTP_200_OK)
