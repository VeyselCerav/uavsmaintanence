from django.db import migrations, models

import apps.documents.models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="file",
            field=models.FileField(
                blank=True,
                upload_to=apps.documents.models.document_upload_to,
            ),
        ),
    ]
