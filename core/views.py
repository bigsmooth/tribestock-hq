from django.http import JsonResponse

def ping(_req):
    return JsonResponse({"ok": True, "service": "tribestock-api"})
