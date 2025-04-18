from django import forms
from .models import User, UserProfile
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('phone',)

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] and cd['password2'] and cd['password1'] != cd['password2']:
            raise ValidationError(_('Passwords do not match'))
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(help_text=_("You can change password using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = User
        fields = ('email', 'phone', 'first_name', 'last_name', 'password', 'is_active', 'is_staff')


class UserRegistrationForm(forms.Form):
    phone = forms.CharField(max_length=11)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise ValidationError(_('This phone number already exists'))
        return phone


class VerifyCodeForm(forms.Form):
    code = forms.IntegerField()


class UserLoginForm(forms.Form):
    phone = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('job', 'avatar', 'age', 'gender')

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Validate image size if necessary
            pass  # Add your custom validation logic here
        return avatar