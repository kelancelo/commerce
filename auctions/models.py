from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Max


class User(AbstractUser):
    # email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username}"


class Category(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"


class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=500)
    starting_bid = models.IntegerField(validators=[MinValueValidator(1)])
    image_url = models.CharField(max_length=200, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="listings", blank=True, null=True)
    listed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=8, choices=[("active", "active"), ("inactive", "inactive")], default="active")
    watchers = models.ManyToManyField(User, blank=True, related_name="watchlist")

    def __str__(self):
        return f"{self.title} - by: {self.listed_by}"

    def get_current_price(self):
        highest_bid = self.bids.aggregate(Max("price"))["price__max"]
        return highest_bid if highest_bid else self.starting_bid


class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    price = models.IntegerField()

    def __str__(self):
        return f"{self.bidder} -> {self.listing}: {self.price}"


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    text = models.CharField(max_length=500)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} -> {self.listing}: {self.text}"
