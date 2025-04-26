from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Comment


class CommentAdminForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = '__all__'
        
    def clean(self):
        cleaned_data = super().clean()
        for field, value in cleaned_data.items():
            setattr(self.instance, field, value)
        try:
            self.instance.clean()
        except ValidationError as e:
            self.add_error(None, e)
            raise e
        return cleaned_data