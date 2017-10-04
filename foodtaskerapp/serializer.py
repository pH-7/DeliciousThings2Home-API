from rest_framework import serializers

from foodtaskerapp.models import Restaurant

class RestaurantSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, restaurant):
        """Get the absolute URL for the logo image"""
        request = self.context.get('request')
        logo_url = restaurant.logo.url

        return request.build_absolute_uri(logo_url)

    class Meta:
        model = Restaurant
        fields = ('id', 'name', 'phone', 'address', 'logo')
