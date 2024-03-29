"""
Author: Pierre-Henry Soria <hi@ph7.me>
Copyright: Pierre-Henry Soria, All Rights Reserved.
"""

from django import forms
from django.contrib.auth.models import User
from foodtaskerapp.models import Restaurant, Meal

class UserForm(forms.ModelForm):
    email = forms.EmailField(max_length=120, required=True)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name', 'email')

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(max_length=120, required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ('name', 'phone', 'address', 'logo')

class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        exclude = ('restaurant',)
