from import_export import resources
from app.models import FuelSale

class FuelSaleResource(resources.ModelResource):
    class Meta:
        model = FuelSale
        # Явно указываем поля (или используем exclude) – зависит от ваших нужд:
        fields = (
            'id',
            'date',
            'organization__name',    # если хотите вывести имя организации вместо id
            'pump__name',            # если хотите вывести имя насоса вместо id
            'quantity',
            'price',
            'total_amount',
            'discount_amount',
            'final_amount',
            'plate_number',
            'new_client',
        )