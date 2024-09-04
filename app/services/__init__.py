from django.shortcuts import get_object_or_404
from django.db.models import Q
from app.utils import *

async def update_model_object(model_obj, update_dict):
    for key, value in update_dict.items():
        setattr(model_obj, key, value)
    model_obj.asave()
