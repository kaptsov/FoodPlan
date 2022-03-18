from django.db import models


class Customer(models.Model):
    username = models.CharField(max_length=25, verbose_name='Имя')
    phone_number = models.CharField(max_length=30, verbose_name="Телефон")
    telegram_id = models.PositiveIntegerField(verbose_name="ID пользователя в телеграмме", unique=True)


class Preference(models.Model):
    type = models.CharField(max_length=30, verbose_name="Предпочтение")


class Subscription(models.Model):
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Подписка")
    register_date = models.DateField()
    paid_until = models.DateField()
    person_amount = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Количество персон")
    preferences = models.ForeignKey(Preference, on_delete=models.CASCADE, verbose_name="Предпочтение")


class Ingredient(models.Model):
    name = models.CharField(max_length=30, verbose_name="Название ингредиента")


class Recipe(models.Model):
    name = models.CharField(max_length=30, verbose_name="Название блюда")
    description = models.TextField()
    image = models.ImageField()
    preferences = models.ManyToManyField(
        Preference,
        through="RecipeClassificator",
        through_fields=("recipe", "preferences"),
        )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        through_fields=("recipe", "ingredient"),
        )


class RecipeClassificator(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    preferences = models.ForeignKey(Preference, on_delete=models.CASCADE)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    ingredient_amount = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Количество ингредиента")
    ingredient_measure = models.CharField(max_length=30, verbose_name="Единица измерения")
