from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Profile, Follower, Playlist

class SearchForm(forms.Form):
    artist = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}))
    from_year = forms.IntegerField(required=False)
    to_year = forms.IntegerField(required=False)

class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_repeat = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    birthday = forms.DateField(widget=forms.TextInput(attrs={'class': 'form-control'}))

class SurveyForm(forms.Form):
   question1 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
   question2 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
   question3 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
   question4 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

class UserUpdateForm(forms.ModelForm):
    # username is required for the database, so we override it here to make it optional to change your username
    username = forms.CharField(required=False)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']

class ProfileUpdateForm(forms.ModelForm):
    # profilepic is required for the database, so we override it here to make it optional to change your profile pic
    profilepic = forms.ImageField(label='Profile Picture', required=False)
    class Meta:
        model = Profile
        fields = ['bio', 'profilepic']
        labels = {'profilepic': ('Profile picture')}

class PlaylistForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = ['title', 'creatorid', 'user']
