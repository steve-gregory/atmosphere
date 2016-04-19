from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models import ApplicationMembership as ImageMembership

class ImageMembershipSerializer(serializers.ModelSerializer):
    """
    This is a 'utility serializer' it should be used for preparing a v2 POST *ONLY*

    This serializer should *never* be returned to the user.
    instead, the core instance should be re-serialized into a 'details serializer'
    """
    project_name = serializers.CharField()
    image = serializers.SlugRelatedField(
        source='application', slug_field='uuid')


    class Meta:
        model = ImageMembership
        fields = (
            'project_name',
            'image',
        )


