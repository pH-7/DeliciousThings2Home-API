from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from foodtaskerapp.models import Meal, Order
from foodtaskerapp.forms import UserForm, RestaurantForm, UserEditForm, MealForm

def home(request):
    return redirect(restaurant_home)

@login_required(login_url='/restaurant/sign-in/')
def restaurant_home(request):
    return redirect(restaurant_order)

@login_required(login_url='/restaurant/sign-in/')
def restaurant_account(request):
    user_form = UserEditForm(instance = request.user)
    restaurant_form = RestaurantForm(instance = request.user.restaurant)

    if request.user.restaurant.logo:
        restaurant_form.fields['logo'].required = False

    if request.method == 'POST':
        # Update the data
        user_form = UserEditForm(request.POST, instance = request.user)
        restaurant_form = RestaurantForm(request.POST, request.FILES, instance = request.user.restaurant)

        if user_form.is_valid() and restaurant_form.is_valid():
            user_form.save()
            restaurant_form.save()

    return render(request, 'restaurant/account.html', {
        'user_form': user_form,
        'restaurant_form': restaurant_form
    })

@login_required(login_url='/restaurant/sign-in/')
def restaurant_meal(request):
    meals = Meal.objects.filter(restaurant = request.user.restaurant).order_by('-id')

    return render(request, 'restaurant/meal.html', {
        'meals': meals
    })

@login_required(login_url='/restaurant/sign-in/')
def restaurant_add_meal(request):
    meal_form = MealForm()

    if request.method == 'POST':
        meal_form = MealForm(request.POST, request.FILES)

        if meal_form.is_valid():
            meal = meal_form.save(commit=False)
            meal.restaurant = request.user.restaurant
            meal.save()
            return redirect(restaurant_meal)

    return render(request, 'restaurant/add-meal.html', {
        'meal_form': meal_form
    })

@login_required(login_url='/restaurant/sign-in/')
def restaurant_edit_meal(request, meal_id):
    meal_form = MealForm(instance = Meal.objects.get(id = meal_id))

    if request.method == 'POST':
        meal_form = MealForm(request.POST, request.FILES, instance = Meal.objects.get(id = meal_id))

        if meal_form.is_valid():
            meal_form.save()
            return redirect(restaurant_meal)

    return render(request, 'restaurant/edit-meal.html', {
        'meal_form': meal_form
    })

@login_required(login_url='/restaurant/sign-in/')
def restaurant_order(request):
    if request.method == 'POST':
        order = Order.objects.get(id = request.POST.get('id'), restaurant = request.user.restaurant)

        if order.status == Order.COOKING:
            order.status = Order.READY
            order.save()

    orders = Order.objects.filter(restaurant = request.user.restaurant).order_by('-id')

    return render(request, 'restaurant/order.html', {'orders': orders})

@login_required(login_url='/restaurant/sign-in/')
def restaurant_report(request):
    return render(request, 'restaurant/report.html', {})

def restaurant_sign_up(request):
    user_form = UserForm()
    restaurant_form = RestaurantForm()

    if request.method == "POST":
        user_form = UserForm(request.POST)
        restaurant_form = RestaurantForm(request.POST, request.FILES)

        if user_form.is_valid() and restaurant_form.is_valid():
            new_user = User.objects.create_user(**user_form.cleaned_data)
            new_restaurant = restaurant_form.save(commit=False) # Just create the object in memory. Not committing to a data
            new_restaurant.user = new_user
            new_restaurant.save() # Save into the DB

            login(request, authenticate(
                username = user_form.cleaned_data['username'],
                password = user_form.cleaned_data['password']
            ))

            # Redirect the user to the homepage
            return redirect(restaurant_home)
        else:
            raise forms.ValidationError('You are already registered.')

    return render(request, 'restaurant/sign-up.html', {
        'user_form': user_form,
        'restaurant_form': restaurant_form
    })
