from django.contrib import admin
from .models import *

class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username")


class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "date_created")

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Category)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Comment)
admin.site.register(Bid)