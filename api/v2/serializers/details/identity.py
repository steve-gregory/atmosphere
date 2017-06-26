from core.models import Identity, Quota
from core.hooks.quota import set_quota_assigned
from rest_framework import serializers
from api.v2.serializers.summaries import (
    QuotaSummarySerializer,
    AllocationSummarySerializer,
    UserSummarySerializer,
    ProviderSummarySerializer
)
from api.v2.serializers.fields.base import UUIDHyperlinkedIdentityField


class IdentitySerializer(serializers.HyperlinkedModelSerializer):
    quota = QuotaSummarySerializer(source='get_quota')
    allocation = AllocationSummarySerializer(source='get_allocation')
    usage = serializers.SerializerMethodField()
    user = UserSummarySerializer(source='created_by')
    provider = ProviderSummarySerializer()
    url = UUIDHyperlinkedIdentityField(
        view_name='api:v2:identity-detail',
    )

    def get_usage(self, identity):
        return identity.get_allocation_usage()

    class Meta:
        model = Identity
        fields = ('id',
                  'uuid',
                  'url',
                  'quota',
                  'allocation',
                  'usage',
                  'provider',
                  'user')


class UpdateIdentitySerializer(IdentitySerializer):
    approved_by = serializers.CharField(write_only=True)
    resource_request = serializers.UUIDField(write_only=True)
    provider = ProviderSummarySerializer(read_only=True)
    user = UserSummarySerializer(source='created_by', read_only=True)

    def update(self, core_identity, validated_data):
        # NOTE: Quota is the _only_ value that can be updated in Identity.
        quota_id = validated_data.get('quota')
        if 'id' in validated_data.get('quota'):
            quota_id = validated_data.get('quota').get('id')
        resource_request_id = validated_data.get('resource_request')
        approved_by = validated_data.get('approved_by')
        quota = Quota.objects.get(id=quota_id)
        set_quota_assigned(core_identity, quota, resource_request_id, approved_by)
        # Synchronous call to EventTable -> Set Quota in the Cloud -> Update the Quota for Identity
        identity = Identity.objects.get(uuid=core_identity.uuid)
        return identity

    class Meta:
        model = Identity
        fields = (
            'id',
            'uuid',
            'url',
            'quota',
            'allocation',
            'usage',
            'provider',
            'user',
            'approved_by',
            'resource_request')
