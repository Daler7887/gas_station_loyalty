from rest_framework import serializers
from django.contrib.auth.models import User
from bot.models import Bot_user
from app.models import Car, FuelSale, PlateRecognition, LoyaltyPointsTransaction


class CameraDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlateRecognition
        fields = ['number', 'image1', 'image2']


class FileUploadSerializer(serializers.Serializer):
    xml = serializers.FileField()
    photo1 = serializers.ImageField()
    photo2 = serializers.ImageField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['plate_number', 'loyalty_points']


class BotUserSerializer(serializers.ModelSerializer):
    car = CarSerializer()

    class Meta:
        model = Bot_user
        fields = ['id', 'user_id', 'username', 'name', 'phone', 'car']


class FuelSaleSerializer(serializers.ModelSerializer):
    organization = serializers.StringRelatedField()
    points = serializers.SerializerMethodField()

    class Meta:
        model = FuelSale
        fields = ['id', 'date', 'organization', 'quantity',
                  'price', 'total_amount', 'discount_amount', 'final_amount', 'plate_number', 'points']

    def get_points(self, obj):
        transaction = LoyaltyPointsTransaction.objects.filter(fuel_sale=obj).first()
        if transaction:
            if transaction.transaction_type == 'accrual':
                return transaction.points
            elif transaction.transaction_type == 'redeem':
                return -transaction.points
        return 0