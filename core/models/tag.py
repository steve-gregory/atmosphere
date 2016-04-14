"""
  Service Tag models for Atmosphere.
"""

from django.db import models
import uuid

class Tag(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.SlugField(max_length=128)
    description = models.CharField(max_length=1024)
    # Not-Null="User-Specific"
    user = models.ForeignKey('AtmosphereUser', null=True, blank=True)

    def in_use(self):
        if self.application_set.count() != 0:
            return True
        elif self.instance_set.count() != 0:
            return True
        return False

    def __unicode__(self):
        return "%s" % (self.name,)

    def json(self):
        return {
            'name': self.name,
            'description': self.description,
            'author': self.user.username if self.user else 'None'
        }

    class Meta:
        db_table = 'tag'
        app_label = 'core'


def updateTags(coreObject, tags, user=None):
    """
    Given a tagged coreObject
    and a list of tags (str, or models.Tag)
    update the coreObject to include *only* these tags.
    """
    from core.models.instance import Instance
    from core.models.application import Application
    from core.models.machine_request import MachineRequest
    # Remove all tags from core*
    for tag in coreObject.tags.all():
        #FIXME: I think this could be done without calling into specific instance-types. using `coreObject.tags.X` instead.
        if isinstance(coreObject, Instance):
            tag.instance_set.remove(coreObject)
        elif isinstance(coreObject, Application):
            tag.application_set.remove(coreObject)
        elif isinstance(coreObject, MachineRequest):
            tag.machinerequest_set.remove(coreObject)
    # Add all tags in tags to core*
    for tag in tags:
        if isinstance(tag, basestring):
            tag = find_or_create_tag(tag, user)
        elif not isinstance(tag, Tag):
            raise TypeError("Expected list of str or Tag, found %s"
                            % type(tag))
        coreObject.tags.add(tag)
    return coreObject


def find_or_create_tag(name, user=None):
    tag = Tag.objects.filter(name__iexact=name)
    if not tag:
        tag = Tag.objects.create(name=name, user=user)
        tag.save()
    else:
        tag = tag[0]
    return tag
