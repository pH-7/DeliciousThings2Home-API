from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

from foodtaskerapp import views, api

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home, name='home'),

    # Restaurant
    url(r'^restaurant/sign-in/$', auth_views.login,
        {'template_name': 'restaurant/sign-in.html'},
        name='restaurant-sign-in'),
    url(r'^restaurant/sign-out/$', auth_views.logout,
        {'next_page': '/'},
        name='restaurant-sign-out'),
    url(r'^restaurant/sign-up/$', views.restaurant_sign_up,
            name='restaurant-sign-up'),
    url(r'^restaurant/$', views.restaurant_home, name='restaurant-home'),
    url(r'^restaurant/account/$', views.restaurant_account,
            name='restaurant-account'),
    url(r'^restaurant/meal/$', views.restaurant_meal,
        name='restaurant-meal'),
    url(r'^restaurant/meal/add/$', views.restaurant_add_meal,
        name='restaurant-add-meal'),
    url(r'^restaurant/meal/edit/(?P<meal_id>\d+)/$', views.restaurant_edit_meal,
        name='restaurant-edit-meal'),
    url(r'^restaurant/order/$', views.restaurant_order,
        name='restaurant-order'),
    url(r'^restaurant/report/$', views.restaurant_report,
        name='restaurant-report'),

    # API Sign-In / Sign-Up / Sign-Out
    # /convert-token (for sign in / sign up)
    # /revoke-token (fir sign out)
    url(r'^api/social/', include('rest_framework_social_oauth2.urls')),

    url(r'^api/customer/restaurants/$', api.customer_get_restaurants),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
