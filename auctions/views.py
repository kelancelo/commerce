from argparse import ArgumentError
from ast import arg
from unicodedata import category
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import *
from .forms import *
from django.db.models import Max

def index(request):
    listings = Listing.objects.filter(status="active")
    # For each active listings, add a "current_price" attribute and set it to whatever's
    # greater between the starting bid and the highest bid if there's any.
    # This approach feels wrong but this is the only way i came up with.
    for listing in listings:
        highest_bid = listing.bids.aggregate(Max("price"))["price__max"]
        current_price = highest_bid if highest_bid else listing.starting_bid
        setattr(listing, "current_price", current_price)
    return render(request, "auctions/index.html", {
        "listings": listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required(login_url="/login")
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save()
            return HttpResponseRedirect(reverse("listing", args=[listing.id]))
        else:
            return render(request, "auctions/create_listing.html", {
                "form": form
            })
    else:
        return render(request, "auctions/create_listing.html", {
            "form": ListingForm(initial={"listed_by": request.user})
        })


def listing(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    if listing.status == "inactive":
        messages.add_message(request, messages.INFO, "Auction is closed.")
    highest_bid = listing.bids.aggregate(Max("price"))["price__max"]
    context = {
        "listing": listing,
        "current_price": listing.starting_bid if not highest_bid else highest_bid,
        }
    # If the user is logged in, the more info they can see.
    if request.user.is_authenticated:
        user_bid = request.user.bids.filter(listing=listing).aggregate(Max("price"))["price__max"]
        user_has_highest_bid = False
        # If the user placed a bid, check if their bid is the highest bid.
        if user_bid:
            if user_bid == highest_bid:
                user_has_highest_bid = True
        # Display message if the logged in user won the auction.
        if listing.status == "inactive" and user_has_highest_bid:
            messages.add_message(request, messages.SUCCESS, "You won the auction!")
        context = {
            **context,
            "bid_count": listing.bids.count(),
            "user_has_highest_bid": user_has_highest_bid,
            "user_created_the_listing": listing.listed_by == request.user,
            "in_watchlist": request.user.watchlist.contains(listing),
            "comments": listing.comments.all().order_by("-date_created"),
            # I stored the form data of bid and comment forms in the session so this view can access
            # it when the bid and comment views redirect back to this view. 
            "bid_form": BidForm(request.session["bid_form"]) if request.session.get("bid_form") else BidForm(initial={"bidder": request.user, "listing": listing}),
            "comment_form": CommentForm(request.session["comment_form"]) if request.session.get("comment_form") else CommentForm(initial={"author": request.user, "listing": listing})
        }
        request.session["bid_form"] = None
        request.session["comment_form"] = None
    return render(request, "auctions/listing.html", context)


@login_required(login_url="/login")
def watchlist(request):
    if request.method == "POST":
        listing_id = request.POST["listing_id"]
        listing = Listing.objects.get(pk=listing_id)
        listing.watchers.add(request.user)
        messages.add_message(request, messages.SUCCESS, "Item added to watchlist!")
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    else:
        # Same approach as with the index view.
        watchlist = request.user.watchlist.all()
        for listing in watchlist:
            highest_bid = listing.bids.aggregate(Max("price"))["price__max"]
            current_price = highest_bid if highest_bid else listing.starting_bid
            setattr(listing, "current_price", current_price) 
        return render(request, "auctions/watchlist.html", {
            "watchlist": watchlist
        })


@login_required(login_url="/login")
def delete_watchlist_item(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    request.user.watchlist.remove(listing)
    messages.add_message(request, messages.SUCCESS, "Item removed from watchlist!")
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))


@login_required(login_url="/login")
@require_POST
def bid(request):
    form = BidForm(request.POST)
    if form.is_valid():
        form.save()
        messages.add_message(request, messages.SUCCESS, "Bid placed successfully!")
    else:
        request.session["bid_form"] = request.POST
    return HttpResponseRedirect(reverse("listing", args=[request.POST["listing"]]))


@login_required(login_url="/login")
def close_auction(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    listing.status = "inactive"
    listing.save()
    messages.add_message(request, messages.SUCCESS, "Auction has been closed!")
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))


@login_required(login_url="/login")
@require_POST
def comment(request):
    form = CommentForm(request.POST)
    if form.is_valid():
        form.save()
    else:
        request.session["comment_form"] = request.POST
    return HttpResponseRedirect(reverse("listing", args=[request.POST["listing"]]))


def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": [{
            **category.__dict__, 
            "item_count": Listing.objects.filter(category=category, status="active").count()
        } for category in Category.objects.all()]
    })


def listings_by_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    listings = Listing.objects.filter(status="active",category=category)
    # Same approach as with index view.
    for listing in listings:
        highest_bid = listing.bids.aggregate(Max("price"))["price__max"]
        current_price = highest_bid if highest_bid else listing.starting_bid
        setattr(listing, "current_price", current_price)
    return render(request, "auctions/listings_by_category.html", {
        "listings": listings,
        "category_name": category.name
    })
