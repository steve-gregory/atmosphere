import pytz
import json

from django.utils.timezone import datetime, now

from threepio import logger

from core.models import Provider, Identity, AtmosphereUser, ProviderMachine
from core.models.application import get_application, create_application, share_application
from core.models.application_version import ApplicationVersion, get_or_create_app_version
from core.models.machine import create_provider_machine
from service.driver import get_account_driver


def from_glance_image(glance_image, provider, tenant_id_to_names={}):
    """
    INPUT: glance_image, Core.Provider
    OUTPUT: Core.ProviderMachine (+Version, +Application, +Membership..)
    """
    identifier = glance_image.get('id')
    try:
        pm = ProviderMachine.objects.get(
            instance_source__provider=provider,
            instance_source__identifier=identifier)
        update_from_glance_image(pm, glance_image)
    except ProviderMachine.DoesNotExist:
        pm = create_from_glance_image(glance_image, provider, tenant_id_to_names)
    return pm


def update_from_glance_image(provider_machine, glance_image):
    """
    Given a provider_machine && glance_image
    Returns a provider machine with latest metadata
    """
    identifier = glance_image.get('id')
    app_name = glance_image.get('application_name')
    app_uuid = glance_image.get('application_uuid')
    app_owner = glance_image.get('application_owner')
    description = glance_image.get('application_description')
    app_tags = glance_image.get('application_tags')
    visibility = glance_image.get('visibility')
    tenant_id = glance_image.get('owner')  # Newer versions of glance..
    version_name = glance_image.get('application_version')
    min_disk = glance_image.get('min_disk')
    min_ram = glance_image.get('min_ram')
    image_size = glance_image.get('size')  # Byte size
    container = glance_image.get('container_format')
    status = glance_image.get('status')
    g_start_date = glance_timestamp(glance_image.get('created_at'))
    g_end_date = glance_timestamp(glance_image.get('deleted'))
    #NOTE: These are some 'simple repairs' that can be made to restore integrity when changes are made behind the scenes.
    attempt_repair_application_description(provider_machine.application, description)
    attempt_repair_version_name(provider_machine.application_version, version_name)
    attempt_repair_start_date(provider_machine, g_start_date)
    attempt_repair_end_date(provider_machine, g_end_date)
    pass


def attempt_repair_end_date(provider_machine, new_end_date=None):
    if not new_end_date:
        return

    instance_source = provider_machine.instance_source
    if not instance_source.end_date:
        instance_source.end_date = new_end_date
        logger.warn("WARNING: ProviderMachine %s *DELETED* from the cloud.. End-dated in the database." % (provider_machine))
        instance_source.save()


def attempt_repair_start_date(provider_machine, new_start_date=None):
    if not new_start_date:
        return

    instance_source = provider_machine.instance_source
    if instance_source.start_date > new_start_date:
        instance_source.start_date = new_start_date
        logger.info("InstanceSource %s start_date update: %s->%s" % (instance_source.id, instance_source.start_date, new_start_date))
        instance_source.save()

    application_version = provider_machine.application_version
    if application_version.start_date > new_start_date:
        application_version.start_date = new_start_date
        logger.info("ApplicationVersion %s start_date update: %s->%s" % (application_version.id, application_version.start_date, new_start_date))
        application_version.save()

    application = provider_machine.application
    if application.start_date > new_start_date:
        logger.info("Application %s start_date update: %s->%s" % (application.id, application.start_date, new_start_date))
        application.start_date = new_start_date
        application.save()
    return True

def attempt_repair_version_name(version, new_name=None):
    """
    """
    if not version or not isinstance(version, ApplicationVersion):
        logger.warn("Expected Core.ApplicationVersion -- Received %s" % version)
        return
    if not new_name:
        return
    if not version.name.startswith('1.0'):
        # Version has likely already been updated. Keep the value to avoid problems
        return
    if new_name.startswith('1.0') and new_name.endswith('0'):
        # Due to a 'bug' in the past with replicated providers, it is common to see: `1.0, 1.0.0, 1.0.0.0`
        # None of these values can be trusted.
        return
    """
    ASSERT: 'New' version name has relevant information,
    and the 'old' name was the "Default" assigned on auto-assignment from the AccountProvider.
    In this situation, we should use the new value.
    """
    ApplicationVersion.rename(version, new_name, archive=True)
    return True


def attempt_repair_application_description(application, new_description=None):
    if not new_description:
        return
    if not application.description.startswith('Imported Application'):
        return
    if new_description.startswith('Imported Application'):
        return
    # ASSERT: 'New' description has relevant information, and the 'old' description was the "Default" assigned on auto-assignment from the AccountProvider.
    # In this situation, we should use the values saved in metadata.
    logger.info("Application %s description update: %s->%s" % (application.id, application.description, new_description))
    application.description = new_description
    application.save()
    return True


def create_from_glance_image(glance_image, provider, tenant_id_to_names={}):
    """
    ROOT: Starting from here, create Core things based on an unknown glance image.
    """
    identifier = glance_image.get('id')
    app_name = _reverse_safe(glance_image.get('application_name'))
    app_uuid = glance_image.get('application_uuid')
    version_name = glance_image.get('application_version')
    app_owner = glance_image.get('application_owner')
    change_log = _reverse_safe(glance_image.get('version_changelog'))
    allow_imaging = glance_image.get('version_allow_imaging', 'true').lower() == 'true'
    visibility = glance_image.get('visibility')
    is_private = (visibility == 'private')
    # Retrieve/Create core things:
    (owner, identity) = _get_owner_from_db(provider, app_owner)
    #1: Get or create an application
    application = get_application(
        provider.uuid, identifier, app_name, app_uuid)
    if not application:
        application = create_app_from_glance_image(glance_image, provider, owner, identity)
    print "Created new application: %s" % application
    #2: Get or create an application version
    version = get_or_create_app_version(
        application, version_name, owner, identity,
        change_log, allow_imaging, identifier)
    print "Created new version: %s" % version
    #3: Get or create a provider machine
    machine = create_provider_machine(identifier, provider.uuid, application, version, identity)
    #4: Include membership on private images
    if is_private:
        member_names = get_membership_from_glance_image(glance_image, provider, tenant_id_to_names)
        share_application(application, provider, member_names)
    print "Created new machine: %s" % machine
    return machine


def _get_owner_from_db(provider, app_owner=None):
    if not app_owner:
        return (None, None)
    try:
        owner = AtmosphereUser.objects.get(username=app_owner)
    except AtmosphereUser.DoesNotExist:
        owner = None
    identity = Identity.objects.filter(created_by__username=owner, provider=provider).first()
    if not identity:
        identity = Identity.objects.filter(
            accountprovider__isnull=False,
            provider=provider).first()
        if identity and not owner:
            owner = identity.created_by
    return (owner, identity)


def get_membership_from_glance_image(glance_image, provider, tenant_map={}):
    """
    Given a *PRIVATE* glance_image, return the list of members
    NOTE: list contains tenant_ids. Conversion to tenant_names required.
    """
    accounts = get_account_driver(provider)
    image_members_list = accounts.image_manager.glance.image_members.list(glance_image.id)
    member_ids = [membership['member_id'] for membership in image_members_list]
    members = []
    for project_id in member_ids:
        project_name = tenant_map.get(project_id)
        if not project_name:
            project = accounts.user_manager.get_project_by_id(project_id)
            project_name = project.name if project else None
        if not project_name:
            print "Could not find project:%s" % project_id
            continue
        members.append(project_name)
        # Remember all-the-things you don't know
        if not tenant_map.get(project_id):
            tenant_map[project_id] = project_name

    return members



def create_app_from_glance_image(glance_image, provider, created_by=None, created_by_identity=None):
    """
    This glance image has no ProviderMachine, so we start by creating the Application.
    """
    identifier = glance_image.get('id')
    app_name = _reverse_safe(glance_image.get('application_name'))
    app_uuid = glance_image.get('application_uuid')
    description = _reverse_safe(glance_image.get('application_description'))
    app_tags = glance_image.get('application_tags', '')
    visibility = glance_image.get('visibility')
    is_private = (visibility == 'private')
    # Attempt to use the original tags
    try:
        tags = json.loads(app_tags)
    except ValueError:
        tags = None
    application = create_application(
        provider.uuid, identifier, app_name,
        created_by_identity, created_by, description,
        is_private, tags, app_uuid)
    return application


def glance_write_machine(provider_machine):
    """
    Using the provider_machine in the DB, save information to the Cloud.
    """
    update_method = ""
    base_source = provider_machine.instance_source
    provider = base_source.provider
    version = provider_machine.application_version
    base_app = provider_machine.application
    identifier = base_source.identifier
    accounts = get_account_driver(provider)
    g_image = glance_image_for(provider.uuid, identifier)
    if not g_image:
        return
    if hasattr(g_image, 'properties'):
        props = g_image.properties
        update_method = 'v2'
    elif hasattr(g_image, 'items'):
        props = dict(g_image.items())
        update_method = 'v3'
    else:
        raise Exception(
            "The method for 'introspecting an image' has changed!"
            " Ask a programmer to fix this!")
    # Do any updating that makes sense... Name. Metadata..
    overrides = {
        "application_version": str(version.name),
        "application_uuid": str(base_app.uuid),
        "application_name": _make_safe(base_app.name),
        "application_owner": base_app.created_by.username,
        "application_tags": json.dumps(
            [_make_safe(tag.name) for tag in base_app.tags.all()]),
        "application_description": _make_safe(base_app.description),
        "version_changelog": _make_safe(version.change_log),
        "version_allow_imaging": str(version.allow_imaging)
    }
    if update_method == 'v2':
        extras = {
            'name': base_app.name,
            'properties': overrides
        }
        props.update(extras)
        g_image.update(props)
    else:
        overrides['name'] = base_app.name
        accounts.image_manager.glance.images.update(
            g_image.id, **overrides)
    return True


# NOTE: If these are being used elsewhere move them to a common place


def _make_safe(unsafe_str):
    """
    REMINDER: Do we allow <br/> in here for HTML rendering of desc/change-log..?
    """
    return unsafe_str.replace("\r\n", "\n").replace("\n", "_LINE_BREAK_")


def _reverse_safe(safe_str):
    if safe_str is None:
        return safe_str
    return safe_str.replace("_LINE_BREAK_", "\n")


def generate_openrc(driver, file_loc):
    project_domain = 'default'
    user_domain = 'default'
    tenant_name = project_name = driver.identity.get_groupname()
    username = driver.identity.get_username()
    password = driver.identity.credentials.get('secret')
    provider_options = driver.provider.options
    if not provider_options:
        raise Exception("Expected to have a dict() 'options' stored in the 'provider' object. Please update this method!")
    if not password:
        raise Exception("Expected to have password stored in the 'secret' credential. Please update this method!")
    identity_api_version = provider_options.get('ex_force_auth_version','2')[0]
    version_prefix = "/v2.0" if ('2' in identity_api_version) else '/v3'
    auth_url = provider_options.get('ex_force_auth_url','') + version_prefix
    openrc_template = \
"""export OS_PROJECT_DOMAIN_ID=%s
export OS_USER_DOMAIN_ID=%s
export OS_PROJECT_NAME=%s
export OS_TENANT_NAME=%s
export OS_USERNAME=%s
export OS_PASSWORD=%s
export OS_AUTH_URL=%s
export OS_IDENTITY_API_VERSION=%s
""" % (project_domain, user_domain, project_name, tenant_name,
       username, password, auth_url, identity_api_version)
    with open(file_loc,'w') as the_file:
        the_file.write(openrc_template)


def glance_update_machine_metadata(provider_machine, metadata={}):
    update_method = ""
    base_source = provider_machine.instance_source
    base_app = provider_machine.application
    identifier = base_source.identifier
    accounts = get_account_driver(provider)
    g_image = glance_image_for(base_source.provider.uuid, identifier)
    if not g_image:
        return False
    if hasattr(g_image, 'properties'):
        props = g_image.properties
        update_method = 'v2'
    elif hasattr(g_image, 'items'):
        props = dict(g_image.items())
        update_method = 'v3'
    else:
        raise Exception(
            "The method for 'introspecting an image' has changed!"
            " Ask a programmer to fix this!")
    overrides = {
        "application_version": str(provider_machine.application_version.name),
        "application_uuid": base_app.uuid,
        "application_name": _make_safe(base_app.name),
        "application_owner": base_app.created_by.username,
        "application_tags": json.dumps(
            [_make_safe(tag.name) for tag in base_app.tags.all()]),
        "application_description": _make_safe(base_app.description)}
    overrides.update(metadata)

    if update_method == 'v2':
        extras = { 'properties': overrides }
        props.update(extras)
        g_image.update(name=base_app.name, properties=extras)
    else:
        accounts.image_manager.glance.images.update(
            g_image.id, **overrides)
    return True



def glance_update_machine(new_machine):
    """
    The glance API contains MOAR information about the image then
    a call to 'list_machines()' on the OpenStack (Compute/Nova) Driver.

    This method will call glance and update any/all available information.
    """
    new_app = new_machine.application
    base_source = new_machine.instance_source

    provider_uuid = base_source.provider.uuid
    identifier = base_source.identifier
    g_image = glance_image_for(provider_uuid, identifier)

    if not g_image:
        logger.warn("DID NOT FIND glance image for %s" % new_machine)
        return

    # If glance image, we can also infer some about the application
    owner = glance_image_owner(provider_uuid, identifier, g_image)
    if owner:
        base_source.created_by = owner.created_by
        base_source.created_by_identity = owner
        base_source.save()

    logger.debug("Found glance image for %s" % new_machine)

    if g_image.get('visibility','public') != 'public':
        new_app.private = True

    if new_app.first_machine() is new_machine:
        logger.debug("Glance image represents App:%s" % new_app)
        new_app.created_by = owner.created_by
        new_app.created_by_identity = owner

    g_start_date = glance_timestamp(g_image.get('created_at'))
    g_end_date = glance_timestamp(g_image.get('deleted'))

    if not g_start_date:
        logger.warn("Could not parse timestamp of 'created_at': %s" % g_image['created_at'])
        g_start_date = now()

    new_app.start_date = g_start_date
    new_app.end_date = g_end_date
    new_app.save()
    base_source.start_date = g_start_date
    base_source.end_date = g_end_date
    base_source.save()
    new_machine.save()


def glance_image_for(provider_uuid, identifier):
    try:
        prov = Provider.objects.get(uuid=provider_uuid)
        accounts = get_account_driver(prov)
        accounts.clear_cache()
        glance_image = accounts.get_image(identifier)
    except Exception as e:
        logger.exception(e)
        glance_image = None
    return glance_image


def glance_image_owner(provider_uuid, identifier, glance_image=None):
    try:
        prov = Provider.objects.get(uuid=provider_uuid)
        accounts = get_account_driver(prov)
        if not glance_image:
            accounts.clear_cache()
            glance_image = accounts.get_image(identifier)
        project = accounts.user_manager.get_project_by_id(glance_image.get('owner'))
    except Exception as e:
        logger.exception(e)
        project = None

    if not project:
        return None
    try:
        image_owner = Identity.objects.get(
            provider__uuid=provider_uuid,
            created_by__username=project.name)
    except Identity.DoesNotExist:
        logger.warn(
            "Could not find a username %s on Provider %s" %
            (project.name, provider_uuid))
        image_owner = None
    return image_owner

def glance_timestamp(iso_8601_stamp):
    if not isinstance(iso_8601_stamp,basestring):
        if iso_8601_stamp:
            logger.debug("Stamp %s could not be parsed" % iso_8601_stamp)
        return None
    append_char = "Z" if iso_8601_stamp.endswith("Z") else ""
    try:
        datetime_obj = datetime.strptime(
            iso_8601_stamp,
            '%Y-%m-%dT%H:%M:%S.%f'+append_char)
    except ValueError:
        try:
            datetime_obj = datetime.strptime(
                iso_8601_stamp,
                '%Y-%m-%dT%H:%M:%S'+append_char)
        except ValueError:
            raise ValueError(
                "Expected ISO8601 Timestamp in Format:"
                " YYYY-MM-DDTHH:MM:SS[.sssss][Z]")
    # All Dates are UTC relative
    datetime_obj = datetime_obj.replace(tzinfo=pytz.utc)
    return datetime_obj
