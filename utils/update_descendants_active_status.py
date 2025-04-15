def update_descendants_active_status(instance):
    descendants = instance.get_descendants(include_self=True)
    descendants.update(is_active=instance.is_active)
