from django.db import models

# Create your models here.


class Customer(models.Model):
    telegram_id = models.IntegerField()
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)

    def __str__(self) -> str:
        return self.name
