from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import ApplicationMembership as ImageMembership
from core.models import Application as Image
from core.models import Group as Membership

from api.v2.serializers.summaries import (
    ImageSummarySerializer, GroupSummarySerializer)
from api.v2.serializers.fields.base import ModelRelatedField


class ImageMembershipSerializer(serializers.HyperlinkedModelSerializer):
    image = ModelRelatedField(
        queryset=Image.objects.all(),
        serializer_class=ImageSummarySerializer,
        style={'base_template': 'input.html'},
        required=False)
    #NOTE: When complete, return here to disambiguate between 'membership'&&'group'
    group = ModelRelatedField(
        queryset=Membership.objects.all(),
        serializer_class=GroupSummarySerializer,
        style={'base_template': 'input.html'},
        lookup_field='uuid',
        required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='api:v2:imageimage_membership-detail',
    )

    class Meta:
        model = ImageMembership
        validators = [
            UniqueTogetherValidator(
                queryset=ImageMembership.objects.all(),
                fields=('image', 'group')
            )
        ]
        fields = (
            'id',
            'url',
            'image',
            'group'
        )
