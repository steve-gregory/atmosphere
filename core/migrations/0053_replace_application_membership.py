# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_remove_version_and_machine_membership'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='applicationmembership',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='applicationmembership',
            name='application',
        ),
        migrations.RemoveField(
            model_name='applicationmembership',
            name='group',
        ),
        migrations.DeleteModel(
            name='ApplicationMembership',
        ),
        migrations.RenameModel(
            old_name='ApplicationMembershipNEW',
            new_name='ApplicationMembership',
        ),
        migrations.AlterModelTable(
            name='applicationmembership',
            table='application_membership',
        ),
    ]
