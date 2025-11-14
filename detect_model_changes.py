from django.db import models

def detect_model_changes(instance: models.Model):
    """
    Detect changes between an existing DB record and its current (unsaved) instance.
    Returns a list of (field_name, old_value, new_value).
    """
    if not instance.pk:
        return []  # New instance, nothing to compare

    try:
        old_instance = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return []

    changed_fields = []
    for field in instance._meta.fields:
        field_name = field.name if not isinstance(field, str) else field
        if field_name.lower() in ("updated", "updated_at"):
            continue
        old_value = getattr(old_instance, field_name)
        new_value = getattr(instance, field_name)

        old_value = None if old_value in (None, "") else old_value
        new_value = None if new_value in (None, "") else new_value

        if old_value != new_value:
            changed_fields.append((field_name, old_value, new_value))

    return changed_fields

def track_model_changes(instance, original_data):
    """
    Compare saved instance (after refresh_from_db) with original pre-save values.
    Returns a readable change log string.
    """
    instance.refresh_from_db()
    updated_data = {field: getattr(instance, field) for field in original_data}

    change_log_lines = []
    for field, old_val in original_data.items():
        field_name = field.name if not isinstance(field, str) else field
        new_val = updated_data[field]
        if field_name.lower() in ("updated", "updated_at"):
            continue

        # Normalize None and empty strings
        old_val = None if old_val in ("", None) else old_val
        new_val = None if new_val in ("", None) else new_val

        if str(old_val) != str(new_val):
            change_log_lines.append(f"{field}: '{old_val}' → '{new_val}'")

    return "; ".join(change_log_lines) if change_log_lines else "No changes detected."
