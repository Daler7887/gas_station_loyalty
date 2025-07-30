from django.contrib import admin
from app.models import *
from app.utils import PLATE_NUMBER_TEMPLATE  # import the regex template
from app.resources import FuelSaleResource
from rangefilter.filters import DateTimeRangeFilter
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

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
            ('valid', 'Действителен'),
            ('invalid', 'Недействителен'),
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


@admin.action(description='Resave fuel sales with filters')
def resave_fuel_sales_with_filters(modeladmin, request, queryset):
    for sale in queryset:
        sale.save()

@admin.register(FuelSale)
class FuelSaleAdmin(ImportExportModelAdmin):
    resource_class = FuelSaleResource

    list_display = (
        'date', 'organization', 'pump', 'quantity',
        'price', 'total_amount', 'discount_amount',
        'final_amount', 'plate_number', 'plate_recognition',
        'new_client'
    )
    list_filter = (
        ('date', DateTimeRangeFilter),
        'organization',
        'pump',
        InvalidPlateFilter,
    )
    search_fields = ['plate_number']
    actions = [fill_plate_numbers, resave_fuel_sales_with_filters]

    # --------------------------------------------
    # Вот эти три строчки — ключ к быстрой форме:
    raw_id_fields = ('organization', 'pump', 'plate_recognition')
    list_select_related = ('organization', 'pump', 'plate_recognition')
    # либо, если вы на Django>=2.0 и настроили search_fields в админах пунктов:
    # autocomplete_fields = ('organization', 'pump', 'plate_recognition')
    # --------------------------------------------

    def has_import_permission(self, request):
        return False


@admin.register(Pump)
class PumpAdmin(admin.ModelAdmin):
    list_display = ['organization', 'number', 'ip_address']
    search_fields = ['number', 'ip_address']


@admin.register(Constant)
class ConstantAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    list_editable = ['value']
    list_display_links = None


@admin.action(description='Delete all loyalty points')
def delete_all_loyalty_points(modeladmin, request, queryset):
    LoyaltyPointsTransaction.objects.all().delete()
    Car.objects.update(loyalty_points=0)

@admin.action(description="Delete cars with invalid plate numbers")
def delete_invalid_plate_numbers(modeladmin, request, queryset):
    queryset.exclude(plate_number__regex=PLATE_NUMBER_TEMPLATE).delete()

@admin.action(description='Resave loyalty points with filters')
def resave_loyalty_points_with_filters(modeladmin, request, queryset):
    for transaction in queryset:
        transaction.save()

@admin.register(LoyaltyPointsTransaction)
class LoyaltyPointsTransactionAdmin(ImportExportModelAdmin):
    list_display = ('organization', 'created_at', 'transaction_type', 'car', 'points',
                    'description', 'created_by')
    list_filter = (('created_at', DateTimeRangeFilter),'transaction_type', 'created_by')
    search_fields = ['car__plate_number', 'description']
    readonly_fields = ('created_by',)
    actions = [delete_all_loyalty_points, resave_loyalty_points_with_filters]

    raw_id_fields = ('fuel_sale', 'car')
    list_select_related = ('fuel_sale', 'car')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_import_permission(self, request):
        return False

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'loyalty_points')
    search_fields = ('plate_number', )
    list_filter = (InvalidPlateFilter, 'plate_number', 'is_blacklisted')
    readonly_fields = ('loyalty_points',)
    actions = [delete_invalid_plate_numbers]


@admin.register(SMBServer)
class SMBServerAdmin(admin.ModelAdmin):
    list_display = ("name", "server_ip", "share_name", "active")
    list_filter = ("active",)
    search_fields = ("name", "server_ip", "share_name")


class OrganizationAccessInline(admin.TabularInline):
    model = OrganizationAccess
    extra = 0


class CustomUserAdmin(BaseUserAdmin):
    inlines = [OrganizationAccessInline]


admin.site.register(OrganizationAccess)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
