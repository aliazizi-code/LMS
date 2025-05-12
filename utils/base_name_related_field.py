from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers



class BaseNameRelatedField(serializers.PrimaryKeyRelatedField):
    model = None
    display_field = 'name'
    
    def to_representation(self, value):
        if value is None:
            return None
            
        if not hasattr(value, self.display_field):
            try:
                if not self.model:
                    raise ValueError("Model must be set")
                    
                value = self.model.objects.get(pk=value.pk)
            except ObjectDoesNotExist:
                return None
            except self.model.DoesNotExist:
                return None
                
        return getattr(value, self.display_field, None)
