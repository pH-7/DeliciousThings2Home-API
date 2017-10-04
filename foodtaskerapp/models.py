"""
Author: Pierre-Henry Soria <hi@ph7.me>
Copyright: Pierre-Henry Soria, All Rights Reserved.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Restaurant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=80)
    address = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='restaurant_logo/', blank=False)

    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    avatar = models.CharField(max_length=500)
    phone = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.user.get_full_name()

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver')
    avatar = models.CharField(max_length=500)
    phone = models.CharField(max_length=500, blank=True)
    address = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.user.get_full_name()

class Meal(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    name = models.CharField(max_length=500)
    short_description = models.CharField(max_length=500)
    image = models.ImageField(upload_to='meal_images/', blank=False)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    COOKING = 1
    READY = 2
    ONTHEWAY = 3
    DELIVERED = 4

    STATUS_CHOICES = (
        (COOKING, 'Cooking'),
        (READY, 'Ready'),
        (READY, 'On the way'),
        (READY, 'Delivered'),
    )

    customer = models.ForeignKey(Customer)
    restaurant = models.ForeignKey(Restaurant)
    driver = models.ForeignKey(Driver)
    address = models.CharField(max_length=120)
    total = models.IntegerField()
    status = models.IntegerField(choices = STATUS_CHOICES)
    created_at = models.DateTimeField(default = timezone.now())
    picked_at = models.DateTimeField(blank = True, null = True)

    def __str__(self):
        return str(self.id)

class OrderDetails(models.Model):
    order = models.ForeignKey(Order, related_name='order_details')
    meal = models.ForeignKey(Meal)
    quantity = models.IntegerField
    sub_total = models.IntegerField()

    def __str__(self):
        return str(self.id)
