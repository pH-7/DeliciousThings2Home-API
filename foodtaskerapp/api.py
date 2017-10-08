"""
Author: Pierre-Henry Soria <hi@ph7.me>
Copyright: Pierre-Henry Soria, All Rights Reserved.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from oauth2_provider.models import AccessToken
import json
import stripe

from foodtaskerapp.models import Restaurant, Meal, Order, OrderDetails, Driver
from foodtaskerapp.serializer import RestaurantSerializer, MealSerializer, OrderSerializer
from foodtaskerapp.util import get_current_weekdays

def customer_get_restaurants(request):
    restaurants = RestaurantSerializer(
        Restaurant.objects.all().order_by('-id'),
        many = True,
        context = {'request': request}
    ).data

    return JsonResponse({"restaurants": restaurants})

def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
        Meal.objects.filter(restaurant_id = restaurant_id).order_by('-id'),
        many = True,
        context = {"request": request}
    ).data

    return JsonResponse({"meals": meals})

@csrf_exempt
def customer_add_order(request):
    """
        params:
            access_token
            restaurant_id
            address
            order_details (in JSON format), example:
                [{"meal_id": 1, "quantity": 2},{"meal_id": 2, "quantity": 3}]
            stripe_token

        return:
            {'status': 'success'}
    """

    if request.method == "POST":
        access_token = get_access_token(request, method = 'POST')

        # Get the profile
        customer = access_token.user.customer

        if Order.objects.filter(customer = customer).exclude(status = Order.DELIVERED):
            return JsonResponse({"status": 'failed', "error": "Your last order must be completed first."})

        # Check the address
        if not request.POST['address']:
            return JsonResponse({"status": "failed", "error": "The address is required."})

        # Get the order details in JSON format
        order_details = json.loads(request.POST.get('order_details'))

        try:
            total_order = 0 # Default total orders value
            for meal in order_details:
                if not Meal.objects.filter(id = meal['meal_id'], restaurant_id = request.POST.get('restaurant_id')):
                    return JsonResponse({"status": "failed", "error": "Meals must be in only one specific restaurant."})
                else:
                    total_order += Meal.objects.get(id = meal['meal_id']).price * meal['quantity']

            if len(order_details) > 0:

                # Firstly, charge customers $$$
                set_stripe_key()

                charge = stripe.Charge.create(
                    # Times by 100 because the amount is in cents
                    amount = total_order * 100,
                    currency = "eur",
                    source = get_stripe_token(request),
                    description = "FoodTasker Order"
                )

                if charge.status != "failed":
                    # Secondly, create an Order
                    order = Order.objects.create(
                        customer = customer,
                        restaurant_id = request.POST.get('restaurant_id'),
                        total = total_order,
                        status = Order.COOKING,
                        address = request.POST.get('address')
                    )

                    # THen, create an Order Details
                    for meal in order_details:
                        OrderDetails.objects.create(
                            order = order,
                            meal_id = meal['meal_id'],
                            quantity = meal['quantity'],
                            sub_total = Meal.objects.get(id = meal['meal_id']).price * meal['quantity']
                        )

                    return JsonResponse({"status": "success"})
                else:
                    return JsonResponse({"status": "failed", "error": "Cannot get Stripe API. Please try again later."})
        except Meal.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "The specified meal doesn't exist."})


def customer_get_latest_order(request):
    access_token = get_access_token(request, method = 'GET')

    customer = access_token.user.customer
    order = OrderSerializer(Order.objects.filter(customer = customer).last()).data

    return JsonResponse({"order": order})

def restaurant_order_notification(request, last_request_time):
    notification = Order.objects.filter(
        restaurant = request.user.restaurant,
        created_at__gt = last_request_time
    ).count()

    return JsonResponse({"notification": notification})

def driver_get_ready_orders(request):
    orders = OrderSerializer(
        Order.objects.filter(status = Order.READY, driver = None).order_by('-id'),
        many = True
    ).data

    return JsonResponse({"orders": orders})

@csrf_exempt
def driver_pick_order(request):
    if request.method == 'POST' and request.POST.get('order_id'):
        access_token = get_access_token(request, method = 'POST')

        driver = access_token.user.driver

        if Order.objects.filter(driver = driver).exclude(status = Order.ONTHEWAY):
            return JsonResponse({"status": "failed", "error": "You can only pick one order at the same time."})

        try:
            order = Order.objects.get(
                id = request.POST.get('order_id'),
                driver = None,
                status = Order.READY
            )
            order.driver = driver
            order.status = Order.ONTHEWAY
            order.picked_at = timezone.now()
            order.save()

            return JsonResponse({"status": "success"})
        except Order.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "This order has been already picked up."})

def driver_get_latest_order(request):
    access_token = get_access_token(request, method = 'GET')

    driver = access_token.user.driver
    order = OrderSerializer(
        Order.objects.filter(driver = driver ).order_by('picked_at').last()
    ).data

    return JsonResponse({"order": order})

@csrf_exempt
def driver_complete_order(request):
    access_token = get_access_token(request, method = 'POST')

    driver = access_token.user.driver

    try:
        order = Order.objects.get(id = request.POST.get('order_id'), driver = driver)

        # Change the order status
        order.status = Order.DELIVERED
        # Then, save it!
        order.save()

        return JsonResponse({"status": "success"})
    except Order.DoesNotExist:
        return JsonResponse({"status": "failed", "error": "This order doesn't exist anymore."})

def driver_get_revenue(request):
    access_token = get_access_token(request, method = 'GET')

    driver = access_token.user.driver

    revenue = {} # dictionary data
    current_weekdays = get_current_weekdays()

    for day in current_weekdays:
        orders = Order.objects.filter(
            driver = driver,
            status = Order.DELIVERED,
            created_at__year = day.year,
            created_at__month = day.month,
            created_at__day = day.day
        )

        revenue[day.strftime("%a")] = sum(order.total for order in orders)

    return JsonResponse({"revenue": revenue})

@csrf_exempt
def driver_update_location(request):
    if request.method == "POST":
        access_token = get_access_token(request, method = 'POST')

        driver = access_token.user.driver

        # Update the location into DB
        driver.location = request.POST.get('location')
        driver.save()

        return JsonResponse({"status": "success"})

def customer_driver_location(request):
    access_token = get_access_token(request, method = 'GET')

    customer = access_token.user.customer

    # Get the driver location frpm this customer's current order
    current_order = Order.objects.filter(
        customer = customer,
        status = Order.ONTHEWAY
    ).last()

    location = current_order.driver.location

    return JsonResponse({"location": location})

def get_access_token(request, method = 'POST'):
    request_name = 'access_token'
    token = request.GET.get(request_name) if method is 'GET' else request.POST.get(request_name)

    access_token = AccessToken.objects.get(
        token = token,
        expires__gt = timezone.now() # Token of the day only
    )

    return access_token


def set_stripe_key():
    from foodtasker.settings import STRIPE_API_SECRET_KEY
    stripe.api_key = STRIPE_API_SECRET_KEY

def get_stripe_token(request):
    request_name = 'stripe_token'

    return request.POST.get(request_name)
