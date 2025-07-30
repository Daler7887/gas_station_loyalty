
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.dateparse import parse_datetime
from app.models import LoyaltyPointsTransaction
from django.db import models
from django.db.models import Q

@require_GET
def get_bonuses_spent(request):
    start_datetime = request.GET.get('startdatetime')
    end_datetime = request.GET.get('enddatetime')
    org_id = request.GET.get('org_id')

    #TODO should check permissions for org_id
    if not org_id:
        return JsonResponse({'error': 'org_id is required'}, status=400)

    if not start_datetime or not end_datetime:
        return JsonResponse({'error': 'startdatetime and enddatetime are required'}, status=400)

    try:
        start_datetime = parse_datetime(start_datetime)
        end_datetime = parse_datetime(end_datetime)
        if not start_datetime or not end_datetime:
            raise ValueError
    except ValueError:
        return JsonResponse({'error': 'Invalid datetime format'}, status=400)

    transactions = LoyaltyPointsTransaction.objects.filter(
        (   Q(fuel_sale__date__range=(start_datetime, end_datetime)) |
            (Q(fuel_sale=None) & Q(created_at__range=(start_datetime, end_datetime)))   
        ),
        organization_id=int(org_id),
        transaction_type='redeem'
    )

    total_bonuses_spent = transactions.aggregate(total=models.Sum('points'))['total'] or 0

    return JsonResponse({'total_bonuses_spent': total_bonuses_spent})