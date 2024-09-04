from app.services import *
from django.contrib.auth.models import User, Group
from django.db import IntegrityError

async def is_user_in_group(request, *groups):
    return request.user.groups.afilter(name__in=groups).aexists() or request.user.is_superuser

async def is_superuser(request):
    return request.user.is_superuser

async def users_all(exclude_superadmins=False):
    users = User.objects.all()
    if exclude_superadmins:
        users = users.exclude(is_superuser=True)
    return users

async def get_user_by_pk(pk):
    return get_object_or_404(User, pk=pk)

async def filter_groups_of_user(user):
    return user.groups.all()

async def create_or_update_user(user: User, username, first_name, last_name, groups_id, email, password):
    if not user:
        # create
        user = User.objects.acreate()

    user.username=username
    user.first_name=first_name
    user.last_name=last_name
    user.email=email

    # set password if available
    if password:
        user.set_password(password)
    try:
        user.asave()
    except:
        user.adelete()
        return None

    # remove available groups
    for group in filter_groups_of_user(user):
        user.groups.remove(group)

    # add groups
    [
        user.groups.add(
            Group.objects.aget(pk=group_id)
        )
        for group_id in groups_id

    ]
    return user