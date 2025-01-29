from django.db import models
from django.core.exceptions import ValidationError


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

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Проверяем, создается ли новая запись
        super().save(*args, **kwargs)

        if is_new and self.plate_recognition:
            # Рассчитываем баллы
            car, created = Car.objects.get_or_create(
                plate_number=self.plate_recognition.number, defaults={'loyalty_points': 0})
            points = self.total_amount * self.get_points_percent() / 100

            # Создаем транзакцию начисления баллов
            LoyaltyPointsTransaction.objects.create(
                car=car,
                organization=self.organization,
                transaction_type='accrual',
                points=points,
                description=f"Начисление за покупку топлива на сумму {self.total_amount}",
                created_by=None
            )

    class Meta:
        ordering = ['-date']

    def get_points_percent(self):
        # Получаем процент начисления баллов
        constant = Constant.objects.filter(key='points_percent').first()
        if constant:
            return int(constant.value)
        return 0

    def __str__(self):
        return f"{self.organization.name} - {self.pump.number} - {self.total_amount}"


class LoyaltyPointsTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('accrual', 'Начисление'),
        ('redeem', 'Списание'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE, null=True)
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, null=True)

    def clean(self):
        # Проверяем баланс перед сохранением
        if self.transaction_type == 'redeem' and self.car.loyalty_points < self.points:
            raise ValidationError(
                f"Недостаточно баллов для списания. Текущий баланс: {self.car.loyalty_points}, "
                f"запрашиваемое списание: {self.points}"
            )

    def save(self, *args, **kwargs):
        # Вызываем clean перед сохранением
        self.full_clean()  # Проверка данных
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.car} - {self.get_transaction_type_display()} {self.points} баллов"


class Car(models.Model):
    plate_number = models.CharField(
        max_length=10, unique=True, verbose_name="Номер автомобиля")
    loyalty_points = models.IntegerField(
        default=0, verbose_name="Баланс")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"{self.plate_number}"
