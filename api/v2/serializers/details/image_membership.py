from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import ApplicationMembership as ImageMembership
from core.models import Application as Image
from core.models import Identity

from api.v2.serializers.summaries import (
    ImageSummarySerializer, IdentitySummarySerializer)
from api.v2.serializers.fields.base import ModelRelatedField


class ImageMembershipSerializer(serializers.HyperlinkedModelSerializer):
    image = ModelRelatedField(
        queryset=Image.objects.all(),
        serializer_class=ImageSummarySerializer,
        style={'base_template': 'input.html'},
        required=False)
    #NOTE: When complete, return here to disambiguate between 'membership'&&'group'
    membership = ModelRelatedField(
        queryset=Identity.objects.all(),
        serializer_class=IdentitySummarySerializer,
        style={'base_template': 'input.html'},
        lookup_field='uuid',
        required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='api:v2:image_membership-detail',
    )

    class Meta:
        model = ImageMembership
        validators = [
            UniqueTogetherValidator(
                queryset=ImageMembership.objects.all(),
                fields=('image', 'membership')
            )
        ]
        fields = (
            'id',
            'url',
            'image',
            'membership'
        )
