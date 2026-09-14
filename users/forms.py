from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):

    username = forms.CharField(max_length=150)

    email = forms.EmailField()

    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8
    )

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'email',
            'full_name',
            'bio',
            'profile_image',
        ]