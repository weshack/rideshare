from django import forms
from django.forms import ModelForm, ValidationError
from rideshare.models import User 

class RegistrationForm(ModelForm):
    password1 = forms.CharField(max_length=30,widget=forms.PasswordInput(attrs={'placeholder': 'Verify Password'}))
    class Meta:
        model = User
        fields = ('name','email','phone_number','password','class_year',)
    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        password1 = cleaned_data.get('password1')
        if password and password1:
            if password != password1:
                raise ValidationError("Passwords do not match.")
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters.")
        else:
            raise ValidationError("Please enter a password.")
        return cleaned_data

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_active = True
        if commit: user.save()
        return user

