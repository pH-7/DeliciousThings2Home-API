from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from oauth2_provider.models import AccessToken

from foodtaskerapp.models import Restaurant, Meal, Order, OrderDetails
from foodtaskerapp.serializer import RestaurantSerializer, MealSerializer

import json

def customer_get_restaurants(request):
    restaurants = RestaurantSerializer(
        Restaurant.objects.all().order_by('-id'),
        many = True,
        context = {'request': request}
    ).data

    return JsonResponse({'restaurants': restaurants})

def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
        Meal.objects.filter(restaurant_id = restaurant_id).order_by('-id'),
        many = True,
        context = {'request': request}
    ).data

    return JsonResponse({'meals': meals})

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
        access_token = AccessToken.objects.get(
            token = request.POST.get('access_token'),
            expires__gt = timezone.now() # Token of the day only
        )

        # Get the profile
        customer = access_token.user.customer

        if Order.objects.filter(customer = customer).exclude(status = Order.DELIVERED):
            return JsonResponse({"status": 'fail', "error": "Your last order must be completed first."})

        # Check the address
        if not request.POST['address']:
            return JsonResponse({"status": "failed", "error": "The address is required."})

        # Get the order details in JSON format
        order_details = json.loads(request.POST['order_details'])

        order_total = 0
        for meal in order_details:
            if not Meal.objects.filter(id = meal['meal_id'], restaurant_id = request.POST['restaurant_id']):
                return JsonResponse({"status": "fail", "error": "Meals must be in only one specific restaurant."})
            else:
                order_total += Meal.objects.get(id = meal['meal_id']).price * meal['quantity']

        if len(order_details) > 0:
            # Firstly, create an Order
            order = Order.objects.create(
                customer = customer,
                restaurant_id = request.POST['restaurant_id'],
                total = order_total,
                status = Order.COOKING,
                address = request.POST['address']
            )

            # THen, create an Order Details
            for meal in order_details:
                OrderDetails.objects.create(
                    order = order,
                    meal_id = meal['meal_id'],
                    quantity = meal['quantity'],
                    sub_total = Meal.objects.get(id = meal['meal_id']).price * meal['quantity']
                )

            return JsonResponse({'status': 'success'})

def customer_get_latest_order(request):
    return JsonResponse({})
