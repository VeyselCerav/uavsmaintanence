from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("technicians", "0002_skill_techniciancertification_technicianskill_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="techniciancertification",
            name="document_id",
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
