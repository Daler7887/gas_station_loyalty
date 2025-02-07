from rest_framework import serializers
from django.contrib.auth.models import User
from bot.models import Bot_user
from app.models import Car, FuelSale, PlateRecognition


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
    plate_number = serializers.CharField(
        source='plate_recognition.number', read_only=True)
    organization = serializers.StringRelatedField()

    class Meta:
        model = FuelSale
        fields = ['id', 'date', 'organization', 'quantity',
                  'price', 'total_amount', 'plate_number']
