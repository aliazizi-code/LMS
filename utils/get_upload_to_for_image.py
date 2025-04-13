from utils.custom_fields.slug_field import slugify

def get_upload_to(instance, filename, prefix):
        slugged_instance = slugify(instance)
        return f'{prefix}/{slugged_instance}'