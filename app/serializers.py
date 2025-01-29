from rest_framework import serializers
from .models import PlateRecognition


class CameraDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlateRecognition
        fields = ['number', 'image1', 'image2']


class FileUploadSerializer(serializers.Serializer):
    xml = serializers.FileField()
    photo1 = serializers.ImageField()
    photo2 = serializers.ImageField()
