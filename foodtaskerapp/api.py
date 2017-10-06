from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from oauth2_provider.models import AccessToken

from foodtaskerapp.models import Restaurant, Meal, Order, OrderDetails
from foodtaskerapp.serializer import RestaurantSerializer, MealSerializer, OrderSerializer

import json

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

        order_total = 0
        for meal in order_details:
            if not Meal.objects.filter(id = meal['meal_id'], restaurant_id = request.POST.get('restaurant_id')):
                return JsonResponse({"status": "failed", "error": "Meals must be in only one specific restaurant."})
            else:
                order_total += Meal.objects.get(id = meal['meal_id']).price * meal['quantity']

        if len(order_details) > 0:
            # Firstly, create an Order
            order = Order.objects.create(
                customer = customer,
                restaurant_id = request.POST.get('restaurant_id'),
                total = order_total,
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

    return JsonResponse({'orders': orders})

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
            return JsonResponse({"status": "failed", "error": "This order has been picked up."})

    return JsonResponse({})

def driver_get_latest_order(request):
    access_token = get_access_token(request, method = 'GET')

    driver = access_token.user.driver
    order = OrderSerializer(
        Order.objects.filter(driver = driver ).order_by('picked_at').last()
    ).data

    return JsonResponse({'order': order})

def driver_complete_order(request):
    return JsonResponse({})

def driver_get_revenue(request):
    return JsonResponse({})

def get_access_token(request, method = 'POST'):
    request_name = 'access_token'
    token = request.GET.get(request_name) if method is 'GET' else request.POST.get(request_name)
    access_token = AccessToken.objects.get(
        token = token,
        expires__gt = timezone.now() # Token of the day only
    )

    return access_token
