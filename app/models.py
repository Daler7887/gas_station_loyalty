from django.db import models
from django.core.exceptions import ValidationError
from app.utils import PLATE_NUMBER_TEMPLATE
from bot.utils.clients import inform_user_sale, inform_changed_balance
import re


class Constant(models.Model):
    key = models.CharField(max_length=50, verbose_name='ключ')
    value = models.TextField(verbose_name='значение')

    class Meta:
        verbose_name = 'Константа'
        verbose_name_plural = 'Константы'


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name="Наименование")
    server = models.ForeignKey(
        'SMBServer', on_delete=models.CASCADE, null=True, verbose_name="Сервер")
    log_path = models.CharField(max_length=255, default='', verbose_name="Путь")
    last_processed_timestamp = models.DateTimeField(
        null=True, blank=True, verbose_name="Последняя обработка")
    loyalty_program = models.BooleanField(
        default=False, verbose_name="Программа лояльности")
    redeem_start_time = models.TimeField(
        null=True, blank=True, verbose_name="Начало периода списания баллов")
    redeem_end_time = models.TimeField(
        null=True, blank=True, verbose_name="Конец периода списания баллов")
    report_chat_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Chat ID для отчетов")

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'
    
    def __str__(self):
        return self.name


class Pump(models.Model):
    number = models.IntegerField(verbose_name="Номер")  # Номер колонки
    ip_address = models.CharField(max_length=15, null=True, blank=True, verbose_name="IP-адрес")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True, verbose_name="Организация")
    public_ip = models.CharField(max_length=15, null=True, blank=True, verbose_name="Публичный IP")
    public_port = models.IntegerField(null=True, blank=True, verbose_name="Публичный порт")
    login = models.CharField(max_length=50, null=True, blank=True, verbose_name="Логин")
    password = models.CharField(max_length=50, null=True, blank=True, verbose_name="Пароль")
    alpr = models.BooleanField(default=False, verbose_name="Распознавание номеров")

    class Meta:
        verbose_name = "Колонка"
        verbose_name_plural = "Колонки"
    def __str__(self):
        return f"Pump {self.number} - {self.organization}"


# Create your models here.
class PlateRecognition(models.Model):
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE, null=True, verbose_name='Колонка')
    number = models.CharField(max_length=20, verbose_name="Номер")
    recognized_at = models.DateTimeField(verbose_name='Время заезда')
    exit_time = models.DateTimeField(null=True, blank=True ,verbose_name='Время выезда')
    image1 = models.ImageField(upload_to='car_images/', null=True, verbose_name="Изображение 1")
    image2 = models.ImageField(upload_to='car_images/', null=True, verbose_name="Изображение 2")
    is_processed = models.BooleanField(default=False, verbose_name="Обработано")
    use_bonus = models.BooleanField(default=False, verbose_name="Использовать бонусы")

    class Meta:
        verbose_name = "Распознование номера"
        verbose_name_plural = "Распознования номера"
        ordering = ['-recognized_at']

    def __str__(self):
        return self.number


class FuelSale(models.Model):
    date = models.DateTimeField(null=True, verbose_name="Дата")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, verbose_name="Организация")
    quantity = models.FloatField(verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая сумма")
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Сумма скидки")
    final_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Итоговая сумма")
    pump = models.ForeignKey(Pump, on_delete=models.PROTECT, null=True, verbose_name="Колонка")
    plate_recognition = models.ForeignKey(
        PlateRecognition, models.PROTECT, null=True, blank=True, verbose_name="Распознавание номера")
    plate_number = models.CharField(max_length=20, null=True, db_index=True, verbose_name="Номер автомобиля")
    new_client = models.BooleanField(default=False, verbose_name="Новый клиент")

    @staticmethod
    def fill_plate_numbers():
        for sale in FuelSale.objects.filter(plate_recognition__isnull=False, plate_number__isnull=True):
            sale.plate_number = sale.plate_recognition.number
            sale.save()

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Проверяем, создается ли новая запись
        if not is_new:
            LoyaltyPointsTransaction.objects.filter(fuel_sale=self).delete()
        self.final_amount = self.total_amount
        self.discount_amount = 0
        super().save(*args, **kwargs)

        if not self.plate_number or not re.match(PLATE_NUMBER_TEMPLATE, self.plate_number):
            return  # Если нет распознавания номера или номер соответствует шаблону, выходим

        car, _ = Car.objects.get_or_create(
                plate_number=self.plate_number, defaults={'loyalty_points': 0, 'is_blacklisted': False})
        car.refresh_from_db() 

        if not self.organization.loyalty_program:
            return

        if car.is_blacklisted:
            # Если автомобиль в черном списке, не начисляем баллы
            return
        
        discount = 0
        points = 0
        use_bonus = self.plate_recognition.use_bonus if self.plate_recognition else False
        if use_bonus and car.loyalty_points > 0:
            # Списываем баллы
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
        else:
            # Рассчитываем баллы
            points = self.total_amount * self.get_points_percent() / 100
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

        self.discount_amount = discount
        self.final_amount = self.total_amount - discount
        super().save(update_fields=['discount_amount', 'final_amount'])

        # Уведомление пользователю о сумме продажи
        if is_new:
            inform_user_sale(car, self.quantity, round(self.final_amount), round(self.total_amount), round(discount), round(points))

        class Meta:
            indexes = [
                models.Index(fields=['plate_number', 'date']),
            ]

    def get_points_percent(self):
        # Получаем процент начисления баллов
        constant = Constant.objects.filter(key='points_percent').first()
        if constant:
            return int(constant.value)
        return 0

    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"

    def __str__(self):
        return f"Продажа #{self.id} - {self.organization} за {self.date.strftime('%d.%m.%Y %H:%M:%S')} на сумму {self.total_amount:.0f}"


class LoyaltyPointsTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('accrual', 'Начисление'),
        ('redeem', 'Списание'),
    ]

    fuel_sale = models.ForeignKey(
        FuelSale, on_delete=models.CASCADE, db_index=True, null=True, blank=True, related_name='bonus_transactions', verbose_name="Продажа топлива")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Организация")
    car = models.ForeignKey('Car', on_delete=models.CASCADE, null=True, verbose_name="Автомобиль")
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPE_CHOICES, verbose_name="Тип транзакции")
    points = models.IntegerField(verbose_name="Баллы")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Создано пользователем")

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

    class Meta:
        verbose_name = "Начисление и списание балов"
        verbose_name_plural = "Начисления и списания балов"

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.car.plate_number} - {self.points} б."


class Car(models.Model):
    plate_number = models.CharField(
        max_length=10, unique=True, verbose_name="Номер автомобиля")
    is_blacklisted = models.BooleanField(
        default=False, verbose_name="В черном списке")
    loyalty_points = models.IntegerField(
        default=0, verbose_name="Баланс")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"

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

    class Meta:
        verbose_name = "Сервер"
        verbose_name_plural = "Сервера"

    def __str__(self):
        return f"{self.name} ({self.server_ip})"


from django.contrib.auth.models import User


class OrganizationAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_accesses')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'organization')


