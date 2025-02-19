from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta


class Constant(models.Model):
    key = models.CharField(max_length=50, verbose_name='ключ')
    value = models.TextField(verbose_name='значение')

    class Meta:
        verbose_name = 'Константа'
        verbose_name_plural = 'Константы'


class Organization(models.Model):
    name = models.CharField(max_length=255)
    server = models.ForeignKey(
        'SMBServer', on_delete=models.CASCADE, null=True)
    log_path = models.CharField(max_length=255, default='')
    last_processed_timestamp = models.DateTimeField(
        null=True, blank=True, verbose_name="Последняя обработка")
    loyalty_program = models.BooleanField(
        default=False, verbose_name="Программа лояльности")

    def __str__(self):
        return self.name


class Pump(models.Model):
    number = models.IntegerField()  # Номер колонки
    ip_address = models.CharField(max_length=15, null=True, blank=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True)
    public_ip = models.CharField(max_length=15, null=True, blank=True)
    public_port = models.IntegerField(null=True, blank=True)
    login = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True)
    alpr = models.BooleanField(default=False)

    def __str__(self):
        return f"Pump {self.number} - {self.organization}"


# Create your models here.
class PlateRecognition(models.Model):
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE, null=True)
    number = models.CharField(max_length=20)
    recognized_at = models.DateTimeField(verbose_name='Время заезда')
    exit_time = models.DateTimeField(null=True, verbose_name='Время выезда')
    image1 = models.ImageField(upload_to='car_images/', null=True)
    image2 = models.ImageField(upload_to='car_images/', null=True)
    is_processed = models.BooleanField(default=False)
    use_bonus = models.BooleanField(default=False)

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
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE, null=True)
    plate_recognition = models.ForeignKey(
        PlateRecognition, on_delete=models.CASCADE, null=True)
    plate_number = models.CharField(max_length=20, null=True)
    new_client = models.BooleanField(default=False)

    @staticmethod
    def fill_plate_numbers():
        for sale in FuelSale.objects.filter(plate_recognition__isnull=False, plate_number__isnull=True):
            sale.plate_number = sale.plate_recognition.number
            sale.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Проверяем, создается ли новая запись
        super().save(*args, **kwargs)

        if is_new and self.organization.loyalty_program and self.plate_number and self.plate_number != 'unknown':
            use_bonus = PlateRecognition.objects.filter(
                pump=self.pump, number=self.plate_number, use_bonus=True, recognized_at__gte=self.date - timedelta(minutes=60)).exists()
            if use_bonus:
                # Списываем баллы
                car = Car.objects.get(plate_number=self.plate_number)
                if car.loyalty_points <= 0:
                    return
                discount = min(car.loyalty_points, self.total_amount)
                # Создаем транзакцию списания баллов
                LoyaltyPointsTransaction.objects.create(
                    car=car,
                    fuel_sale=self,
                    organization=self.organization,
                    transaction_type='redeem',
                    points=discount,
                    description=f"Потрачено балов для покупки топлива на сумму {self.total_amount}",
                    created_by=None
                )
                self.discount_amount = discount
                self.final_amount = self.total_amount - discount
                super().save(update_fields=['discount_amount', 'final_amount'])
            else:
                # Рассчитываем баллы
                points = self.total_amount * self.get_points_percent() / 100
                car, created = Car.objects.get_or_create(
                    plate_number=self.plate_number, defaults={'loyalty_points': 0})

                if points > 0:
                    # Создаем транзакцию начисления баллов
                    LoyaltyPointsTransaction.objects.create(
                        car=car,
                        fuel_sale=self,
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
        return f"Продажа #{self.id} - {self.organization} за {self.date.strftime('%d.%m.%Y %H:%M:%S')} на сумму {self.total_amount:.0f}"


class LoyaltyPointsTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('accrual', 'Начисление'),
        ('redeem', 'Списание'),
    ]

    fuel_sale = models.ForeignKey(
        FuelSale, on_delete=models.CASCADE, null=True, blank=True, related_name='bonus_transactions')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE, null=True)
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, null=True, blank=True)

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
        return f"{self.get_transaction_type_display()} - {self.car.plate_number} - {self.points} б."


class Car(models.Model):
    plate_number = models.CharField(
        max_length=10, unique=True, verbose_name="Номер автомобиля")
    loyalty_points = models.IntegerField(
        default=0, verbose_name="Баланс")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"{self.plate_number}"


class SMBServer(models.Model):
    name = models.CharField(max_length=255, unique=True,
                            verbose_name="Название сервера")
    server_ip = models.GenericIPAddressField(verbose_name="IP-адрес сервера")
    share_name = models.CharField(
        max_length=255, verbose_name="Имя расшаренной папки")
    username = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Логин")
    password = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Пароль")
    active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return f"{self.name} ({self.server_ip})"
