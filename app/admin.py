from django.contrib import admin
from app.models import *


# Register your models here.
@admin.register(PlateRecognition)
class PlateNumberAdmin(admin.ModelAdmin):
    list_display = ('pump', 'number', 'recognized_at', 'image1', 'image2', 'is_processed')
    search_fields = ('number', )
    list_filter = ('pump', 'recognized_at',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'log_path', 'loyalty_program')


@admin.register(FuelSale)
class FuelSaleAdmin(admin.ModelAdmin):
    list_display = ('date', 'organization', 'pump', 'quantity',
                    'price', 'total_amount', 'plate_recognition', 'new_client')
    list_filter = ('organization', 'pump')


@admin.register(Pump)
class PumpAdmin(admin.ModelAdmin):
    list_display = ['organization', 'number', 'ip_address']
    search_fields = ['number', 'ip_address']


@admin.register(Constant)
class ConstantAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']


@admin.register(LoyaltyPointsTransaction)
class LoyaltyPointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'created_at', 'transaction_type', 'car', 'points',
                    'description', 'created_by')
    # Поле только для чтения, чтобы пользователь не мог его редактировать
    readonly_fields = ('created_by',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
            super().save_model(request, obj, form, change)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'loyalty_points')
    search_fields = ('plate_number', )
    list_filter = ('loyalty_points', )


@admin.register(SMBServer)
class SMBServerAdmin(admin.ModelAdmin):
    list_display = ("name", "server_ip", "share_name", "active")
    list_filter = ("active",)
    search_fields = ("name", "server_ip", "share_name")
