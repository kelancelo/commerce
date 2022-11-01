from django import forms
from .models import *
from django.db.models import Max
from django.core.exceptions import ValidationError

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "description", "starting_bid",
                  "image_url", "category"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control mb-3"}),
            "description": forms.Textarea(attrs={"class": "form-control mb-3"}),
            "starting_bid": forms.NumberInput(attrs={"class": "form-control mb-3"}),
            "image_url": forms.TextInput(attrs={"class": "form-control mb-3"}),
            "category": forms.Select(attrs={"class": "form-control mb-3"}),
        }


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ["listing", "price"]
        widgets = {
            "listing": forms.HiddenInput(),
            "price": forms.NumberInput(attrs={"class": "form-control form-control-sm", "placeholder": "Bid"})
        }
        labels = {
            "price": ""
        }

    def clean(self):
        cleaned_data = super().clean()
        listing = cleaned_data["listing"]
        price = cleaned_data["price"]
        highest_bid = listing.bids.aggregate(Max("price"))["price__max"]
        if highest_bid:
            if price <= highest_bid:
                self.add_error("price", "Bid must be greater than any other bids.")
        elif price < listing.starting_bid:
                self.add_error("price", "Bid must be at least equal to the starting bid.")
        


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["listing", "text"]
        widgets = {
            "listing": forms.HiddenInput(),
            "text": forms.Textarea(attrs={
                "class": "form-control mb-2", 
                "placeholder": "Write a comment...",
                "rows": 2
            })
        }
        labels = {
            "text": ""
        }