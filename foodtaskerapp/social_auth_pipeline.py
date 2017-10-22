from foodtaskerapp.models import Customer, Driver

FB_GRAPH_AVATAR_URL = 'https://graph.facebook.com/%s/picture?type=large'

def create_user_by_type(backend, user, request, response, *arg, **kwargs):
    if backend.name == 'facebook':
        avatar = FB_GRAPH_AVATAR_URL % response['id']

    if request['user_type'] == 'driver' and not Driver.objects.filter(user_id=user.id):
        Driver.objects.create(user_id=user.id, avatar=avatar)
    elif not Customer.objects.filter(user_id=user.id):
        Customer.objects.create(user_id=user.id, avatar=avatar)
