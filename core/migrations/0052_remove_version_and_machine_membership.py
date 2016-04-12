# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_non_null_key_instance_action'),
    ]

    operations = [
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
        migrations.AlterUniqueTogether(
            name='providermachinemembership',
            unique_together=set([]),
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
        migrations.AddField(
            model_name='applicationmembership',
            name='member',
            field=models.ForeignKey(related_name='shared_applications', default=1, to='core.Identity'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='applicationmembership',
            name='application',
            field=models.ForeignKey(related_name='membership', to='core.Application'),
        ),
        migrations.AlterUniqueTogether(
            name='applicationmembership',
            unique_together=set([('application', 'member')]),
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
        migrations.RemoveField(
            model_name='applicationmembership',
            name='can_edit',
        ),
        migrations.RemoveField(
            model_name='applicationmembership',
            name='group',
        ),
    ]
