from django.core.exceptions import ValidationError
from django.conf import settings


def validate_image_size(image, size=settings.IMAGE_SIZES["DEFAULT_ALL_IMAGE_SIZE_LIMIT"]):
    max_size = size * 1024

    if image.size > max_size:
        raise ValidationError(f'Image size must be less than {max_size/1024} kb')


# def validate_image_dimensions(image, max_value=1280, min_value=640):
#     width = image.width
#     height = image.height

#     if width > max_value or height > max_value:
#         raise ValidationError(f'Image dimensions must be less than {max_value}x{max_value} pixels')
    
#     if width < min_value or height < min_value:
#         raise ValidationError(f'Image dimensions must be greater than {min_value}x{min_value} pixels')
    
#     if width != height:
#         raise ValidationError('Image dimensions must be square')
