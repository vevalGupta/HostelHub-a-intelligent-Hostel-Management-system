from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm # inbuild feature of django to create user registration form
from .models import Complaint

class UserRegisterForm(UserCreationForm):
    email =forms.EmailField(required=True,label='Gmail')# this created the email part with stating that it is compulsory to fill
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2'] # this is the order of the fields that will be shown in the registration form

    # ther is an another way to create form is by using form.form
"""
class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=15)
    email = forms.EmailField()
    password = forms.CharField()
"""
    # check whether the email exist in db or not
def clean_email(self):
    email = self.cleaned_data.get('email', label="Gmail")
    if User.objects.filter(email=email).exists():# method predefined to filter the gmail exists
            raise forms.ValidationError("Email already exists")
    return email


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'subject', 'description', 'attachment']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full bg-[#F8F7FD] border-none rounded-xl p-4 text-sm text-gray-600 focus:ring-2 focus:ring-purple-400 outline-none'}),
            'subject': forms.TextInput(attrs={'class': 'w-full bg-[#F8F7FD] border-none rounded-xl p-4 text-sm focus:ring-2 focus:ring-purple-400 outline-none', 'placeholder': 'Enter subject'}),
            'description': forms.Textarea(attrs={'class': 'w-full bg-[#F8F7FD] border-none rounded-xl p-4 text-sm focus:ring-2 focus:ring-purple-400 outline-none', 'placeholder': 'Describe your issue or concern...', 'rows': 3}),
            'attachment': forms.FileInput(attrs={'class': 'w-full bg-[#F8F7FD] border-none rounded-xl p-4 text-sm focus:ring-2 focus:ring-purple-400 outline-none'}),
        }
    

    