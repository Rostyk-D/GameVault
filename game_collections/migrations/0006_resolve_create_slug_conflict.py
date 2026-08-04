from django.db import migrations


def resolve_create_slug_conflict(apps, schema_editor):
    GameCollection = apps.get_model("game_collections", "GameCollection")

    for collection in GameCollection.objects.filter(slug="create"):
        slug = "create-1"
        suffix_number = 2

        while GameCollection.objects.filter(slug=slug).exclude(pk=collection.pk).exists():
            slug = f"create-{suffix_number}"
            suffix_number += 1

        collection.slug = slug
        collection.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("game_collections", "0005_gamecollection_slug"),
    ]

    operations = [
        migrations.RunPython(
            resolve_create_slug_conflict,
            migrations.RunPython.noop,
        ),
    ]
