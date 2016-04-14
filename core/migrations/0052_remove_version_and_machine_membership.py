# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_membership(apps, schema):
    ApplicationMembership = apps.get_model("core", "ApplicationMembership")
    ApplicationMembershipNEW = apps.get_model("core", "ApplicationMembershipNEW")
    for membership in ApplicationMembership.objects.all():
        app = membership.application
        group = membership.group
        for identity in group.identities.all():
            ApplicationMembershipNEW.objects.get_or_create(application=app, member=identity)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_non_null_key_instance_action'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationMembershipNEW',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('application', models.ForeignKey(related_name='membership', to='core.Application')),
                ('member', models.ForeignKey(related_name='shared_applications', to='core.Identity')),
            ],
            options={
                'db_table': 'application_membership_new',
            },
        ),
        migrations.AlterUniqueTogether(
            name='applicationversionmembership',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='applicationversionmembership',
            name='group',
        ),
        migrations.RemoveField(
            model_name='applicationversionmembership',
            name='image_version',
        ),
        migrations.AlterUniqueTogether(
            name='instancemembership',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='instancemembership',
            name='instance',
        ),
        migrations.RemoveField(
            model_name='instancemembership',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='providermachinemembership',
            name='group',
        ),
        migrations.RemoveField(
            model_name='providermachinemembership',
            name='provider_machine',
        ),
        migrations.RemoveField(
            model_name='applicationversion',
            name='membership',
        ),
        migrations.RemoveField(
            model_name='group',
            name='applications',
        ),
        migrations.RemoveField(
            model_name='group',
            name='instances',
        ),
        migrations.RemoveField(
            model_name='group',
            name='provider_machines',
        ),
        migrations.DeleteModel(
            name='ApplicationVersionMembership',
        ),
        migrations.DeleteModel(
            name='InstanceMembership',
        ),
        migrations.DeleteModel(
            name='ProviderMachineMembership',
        ),
        migrations.AlterUniqueTogether(
            name='applicationmembershipnew',
            unique_together=set([('application', 'member')]),
        ),
        migrations.RunPython(
            migrate_membership, None
        ),
    ]
