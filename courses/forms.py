from django.contrib import admin
from django_json_widget.widgets import JSONEditorWidget
from .models import CourseRequest
from django import forms


class CourseRequestForm(forms.ModelForm):
    class Meta:
        model = CourseRequest
        fields = '__all__'
        widgets = {
            'data': JSONEditorWidget(attrs={
                'style': """
                    font-family: Vazir;
                    direction: rtl;
                    width: 100%;
                    max-height: 1000px;
                    min-height: 600px;
                """
            })
        }
