from django.contrib import admin

from .models import Customer
from .models import Preference
from .models import Subscription
from .models import Ingredient
from .models import Recipe
from .models import RecipeClassificator
from .models import RecipeIngredient

admin.site.register(Customer)
admin.site.register(Preference)
admin.site.register(Subscription)
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeClassificator)
admin.site.register(RecipeIngredient)
