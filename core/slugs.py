from django.utils.text import slugify


def create_unique_slug(
    instance,
    value,
    field_name="slug",
    fallback="item",
    reserved_slugs=(),
):
    """Create a URL-safe, unique slug that fits the model field length."""
    field = instance._meta.get_field(field_name)
    max_length = field.max_length
    base_slug = slugify(value) or fallback
    base_slug = base_slug[:max_length]
    slug = base_slug
    suffix_number = 1
    queryset = instance.__class__._default_manager.exclude(pk=instance.pk)

    while slug in reserved_slugs or queryset.filter(
        **{field_name: slug}
    ).exists():
        suffix = f"-{suffix_number}"
        slug = f"{base_slug[:max_length - len(suffix)]}{suffix}"
        suffix_number += 1

    return slug
