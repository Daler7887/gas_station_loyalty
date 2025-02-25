from django.contrib import admin
from app.models import *
from app.utils import PLATE_NUMBER_TEMPLATE  # import the regex template
import re


# Register your models here.
class InvalidPlateRecognitionFilter(admin.SimpleListFilter):
    title = 'Plate Number Validity'
    parameter_name = 'plate_valid'

    def lookups(self, request, model_admin):
        return (
            ('valid', 'Valid'),
            ('invalid', 'Invalid'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'valid':
            return queryset.filter(number__regex=PLATE_NUMBER_TEMPLATE)
        if self.value() == 'invalid':
            return queryset.exclude(number__regex=PLATE_NUMBER_TEMPLATE)
        return queryset


class InvalidPlateFilter(admin.SimpleListFilter):
    title = 'Plate Number Validity'
    parameter_name = 'plate_valid'

    def lookups(self, request, model_admin):
        return (
            ('valid', 'Valid'),
            ('invalid', 'Invalid'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'valid':
            return queryset.filter(plate_number__regex=PLATE_NUMBER_TEMPLATE)
        if self.value() == 'invalid':
            return queryset.exclude(plate_number__regex=PLATE_NUMBER_TEMPLATE)
        return queryset


@admin.register(PlateRecognition)
class PlateNumberAdmin(admin.ModelAdmin):
    list_display = ('pump', 'number', 'recognized_at',
                     'image2', 'is_processed', 'use_bonus')
    search_fields = ('number', )
    list_filter = ('pump', 'recognized_at', 'is_processed', 'use_bonus', InvalidPlateRecognitionFilter)


@admin.action(description='Fill plate numbers for old records')
def fill_plate_numbers(modeladmin, request, queryset):
    FuelSale.fill_plate_numbers()


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'log_path', 'loyalty_program')


@admin.register(FuelSale)
class FuelSaleAdmin(admin.ModelAdmin):
    list_display = ('date', 'organization', 'pump', 'quantity',
                    'price', 'total_amount', 'discount_amount', 'final_amount', 'plate_number', 'plate_recognition', 'new_client')
    list_filter = ('organization', 'pump', 'date', InvalidPlateFilter)
    actions = [fill_plate_numbers]


@admin.register(Pump)
class PumpAdmin(admin.ModelAdmin):
    list_display = ['organization', 'number', 'ip_address']
    search_fields = ['number', 'ip_address']


@admin.register(Constant)
class ConstantAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']


@admin.action(description='Delete all loyalty points')
def delete_all_loyalty_points(modeladmin, request, queryset):
    LoyaltyPointsTransaction.objects.all().delete()
    Car.objects.update(loyalty_points=0)

@admin.action(description="Delete cars with invalid plate numbers")
def delete_invalid_plate_numbers(modeladmin, request, queryset):
    queryset.exclude(plate_number__regex=PLATE_NUMBER_TEMPLATE).delete()

@admin.register(LoyaltyPointsTransaction)
class LoyaltyPointsTransactionAdmin(admin.ModelAdmin):
    list_display = ('organization', 'created_at', 'transaction_type', 'car', 'points',
                    'description', 'created_by')
    list_filter = ('transaction_type', 'car', 'created_by')
    readonly_fields = ('created_by',)
    actions = [delete_all_loyalty_points]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'loyalty_points')
    search_fields = ('plate_number', )
    list_filter = (InvalidPlateFilter,)
    actions = [delete_invalid_plate_numbers]


@admin.register(SMBServer)
class SMBServerAdmin(admin.ModelAdmin):
    list_display = ("name", "server_ip", "share_name", "active")
    list_filter = ("active",)
    search_fields = ("name", "server_ip", "share_name")
