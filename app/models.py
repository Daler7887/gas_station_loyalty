from django.db import models


class Constant(models.Model):
    key = models.CharField(max_length=50, verbose_name='ключ')
    value = models.TextField(verbose_name='значение')

    class Meta:
        verbose_name = 'Константа'
        verbose_name_plural = 'Константы'


class Organization(models.Model):
    name = models.CharField(max_length=255)
    log_path = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.name


class Pump(models.Model):
    number = models.IntegerField()  # Номер колонки
    ip_address = models.CharField(max_length=15, null=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Pump {self.number} - {self.organization}"


class LogProcessingMetadata(models.Model):
    last_processed_timestamp = models.DateTimeField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Last processed log timestamp for {self.organization} : {self.last_processed_timestamp}"


# Create your models here.
class PlateRecognition(models.Model):
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE, null=True)
    number = models.CharField(max_length=20)
    recognized_at = models.DateTimeField()
    image1 = models.ImageField(upload_to='car_images/', null=True)
    image2 = models.ImageField(upload_to='car_images/', null=True)

    class Meta:
        ordering = ['-recognized_at']

    def __str__(self):
        return self.number


class FuelSale(models.Model):
    date = models.DateTimeField(null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    quantity = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE, null=True)
    plate_recognition = models.ForeignKey(
        PlateRecognition, on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.organization.name} - {self.pump.number} - {self.total_amount}"
