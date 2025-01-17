from django.contrib import admin
from app.models import *

# Register your models here.
@admin.register(PlateRecognition)
class PlateNumberAdmin(admin.ModelAdmin):
    list_display = ('pump','number', 'recognized_at', 'image1', 'image2')
    search_fields = ('number', )
    list_filter = ('pump','recognized_at',)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'log_path')
    

@admin.register(FuelSale)
class FuelSaleAdmin(admin.ModelAdmin):
    list_display = ('date','organization', 'pump','quantity', 'price','total_amount', 'plate_recognition')
    list_filter = ('organization', 'pump')

@admin.register(Pump)
class PumpAdmin(admin.ModelAdmin):
    list_display = ['number', 'organization', 'ip_address']
    search_fields = ['number', 'ip_address']

@admin.register(Constant)
class ConstantAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']


admin.site.register(LogProcessingMetadata)