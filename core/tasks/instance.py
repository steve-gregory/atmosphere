from celery.decorators import periodic_task
from celery.task.schedules import crontab

from atmosphere.logger import logger
from datetime import datetime

@periodic_task(run_every=crontab(hour='*', minute='*/5', day_of_week='*'))
def test_all_instance_links():
    try:
        #logger.debug("test_all_instance_links task started at %s." % datetime.now())
        instances = get_all_instances()
        update_links(instances)
        #logger.debug("test_all_instance_links task finished at %s." % datetime.now())
    except Exception as exc:
        logger.warn(exc)
        test_all_instance_links.retry(exc=exc)

def get_all_instances():
    from core.models import Identity, Provider
    from api import getEshDriver
    all_instances = []
    for provider in Provider.objects.all():
        identity_list = Identity.objects.filter(provider=provider)
        if not identity_list:
            continue
        identity = identity_list[0]
        driver = getEshDriver(identity)
        meta_driver = driver.provider.metaCls(driver)
        all_instances.extend(meta_driver.all_instances())
    return all_instances

def update_links(instances):
    from core.models import Instance
    from service.linktest import active_instances
    updated = []
    linktest_results = active_instances(instances)
    for (instance_id, link_results) in linktest_results.items():
        try:
            update = False
            instance = Instance.objects.get(provider_alias=instance_id)
            if link_results['shell'] != instance.shell:
                logger.debug('Change Instance %s shell %s-->%s' %
                        (instance.provider_alias, instance.shell,
                            link_results['shell']))
                instance.shell = link_results['shell']
                update = True
            if link_results['vnc'] != instance.vnc:
                logger.debug('Change Instance %s VNC %s-->%s' %
                        (instance.provider_alias, instance.vnc,
                            link_results['vnc']))
                instance.vnc = link_results['vnc']
                update = True
            if update:
                updated.append(instance)
                instance.save()
        except Instance.DoesNotExist:
            continue
    logger.debug("Instances updated: %d" % len(updated))
    return updated