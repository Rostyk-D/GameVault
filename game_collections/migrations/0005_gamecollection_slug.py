from django.db import migrations, models
from django.utils.text import slugify


def populate_collection_slugs(apps, schema_editor):
    GameCollection = apps.get_model("game_collections", "GameCollection")

    for collection in GameCollection.objects.order_by("pk"):
        base_slug = slugify(collection.title) or "collection"
        slug = base_slug[:120]
        suffix_number = 1

        while (
            slug == "create"
            or GameCollection.objects.filter(slug=slug).exclude(pk=collection.pk).exists()
        ):
            suffix = f"-{suffix_number}"
            slug = f"{base_slug[:120 - len(suffix)]}{suffix}"
            suffix_number += 1

        collection.slug = slug
        collection.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("game_collections", "0004_remove_collectiongame_rating_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="gamecollection",
            name="slug",
            field=models.SlugField(blank=True, max_length=120, null=True),
        ),
        migrations.RunPython(populate_collection_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="gamecollection",
            name="slug",
            field=models.SlugField(blank=True, max_length=120, unique=True),
        ),
    ]
