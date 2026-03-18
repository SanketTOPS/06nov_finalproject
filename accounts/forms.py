from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserSignUpForm(UserCreationForm):
    fullname = forms.CharField(max_length=100, required=True)
    mobile = forms.CharField(max_length=15, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('fullname', 'email', 'mobile')
