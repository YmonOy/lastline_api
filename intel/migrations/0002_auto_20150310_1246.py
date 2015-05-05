# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('intel', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='apisession',
            old_name='session',
            new_name='serialized',
        ),
    ]
