from django.http import HttpResponse

def api_root(request):
    return HttpResponse("Welcome to the Cauldron Plugin Registry API. Access /api/ for endpoints.")