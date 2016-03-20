import logging
from django.db.models.signals import post_save
from channels import Group
from json import dumps
from .models import (
    UserProfile, AtmosphereUser,
    Instance, Volume, ProviderMachine
)


# Save Hooks Here:
def get_or_create_user_profile(sender, instance, created, **kwargs):
    logger = logging.getLogger(__name__)
    prof = UserProfile.objects.get_or_create(user=instance)
    if prof[1] is True:
        logger.debug("Creating User Profile for %s" % instance)

# Instantiate the hooks:
post_save.connect(get_or_create_user_profile, sender=AtmosphereUser)


def send_notification(notification):
    logger = logging.getLogger(__name__)
    logger.info('send_notification. notification = %s', notification)
    Group("notifications").send({'text': dumps(notification)})
