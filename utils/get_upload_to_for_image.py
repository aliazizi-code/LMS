from utils.slug_field import slugify

def get_upload_to(instance, filename, prefix):
        slugged_filename = slugify(filename)
        slugged_instance = slugify(instance)
        return f'{prefix}/{slugged_instance}/{slugged_filename}'