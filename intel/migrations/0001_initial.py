# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='APISession',
            fields=[
                ('login_uri', models.CharField(max_length=1024, serialize=False, verbose_name=b'Login URI', primary_key=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'Last modified')),
                ('session', models.BinaryField(verbose_name=b'Serialized session')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
