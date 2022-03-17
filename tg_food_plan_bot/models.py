from django.db import models


class Customers(models.Model):
    username = models.CharField(max_length=25, verbose_name = 'Имя')
    phone_number = models.CharField(max_length=30, verbose_name = "Телефон")
    telegram_id = models.PositiveIntegerField(verbose_name="ID пользователя в телеграмме", unique=True)


class Preferences(models.Model):
    type = models.CharField(max_length=30, verbose_name = "Предпочтение")


class Subscription(models.Model):
    owner = models.ForeignKey(user, on_delete=models.CASCADE, verbose_name="Подписка")
    register_date = models.DateField()
    paid_until = models.DateField()
    person_amount = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Количество персон")
    preferences = models.ForeignKey(preferences, on_delete=models.CASCADE, versbose_name="Предпочтение")

