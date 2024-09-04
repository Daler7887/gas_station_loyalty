from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import resolve_url
from django.conf import settings
from app.services.user_service import *

async def go_to_login(request):
    path = await request.get_full_path()
    return redirect_to_login(path)

async def group_required(*groups):
    async def decorator(function):
        async def wrapper(request, *args, **kwargs):
            if is_user_in_group(request, *groups):
                return function(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator