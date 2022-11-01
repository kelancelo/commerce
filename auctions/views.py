from django.contrib.auth import login
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator

from .models import *
from .forms import *
from django.db.models import Max


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all()
    })


def active_listings(request):
    return render(request, "auctions/active_listings.html", {
        "listings": Listing.objects.filter(status="active")
    })


@login_required()
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = Listing.objects.create(**form.cleaned_data, listed_by=request.user)
            listing.save()
            return HttpResponseRedirect(reverse("listing", args=[listing.id]))
        else:
            return render(request, "auctions/create_listing.html", {
                "form": form
            }, status=400)
    else:
        return render(request, "auctions/create_listing.html", {
            "form": ListingForm(initial={"listed_by": request.user})
        })


def listing(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    highest_bid = listing.bids.aggregate(Max("price"))["price__max"]
    comments = listing.comments.order_by("-date_created")
    page_num = request.GET.get("page")
    if not page_num:
        page_num = 1
    paginator = Paginator(comments, 5)
    comment_page = paginator.get_page(page_num)
    context = {
        "listing": listing,
        "current_price": listing.starting_bid if not highest_bid else highest_bid,
        "comment_page": comment_page
    }
    # If the user is logged in, the more info they can see.
    if request.user.is_authenticated:
        user_has_highest_bid = False
        if listing.listed_by != request.user:
            user_bid = request.user.bids.filter(listing=listing).aggregate(Max("price"))["price__max"]
            # If the user placed a bid, check if their bid is the highest bid.
            if user_bid:
                if user_bid == highest_bid:
                    user_has_highest_bid = True
        # Display message if the logged in user won the auction.
        if listing.status == "inactive":
            if user_has_highest_bid:
                messages.add_message(request, messages.SUCCESS, "You won the auction!")
            else:
                messages.add_message(request, messages.SUCCESS, "Auction is closed.")        
            return render(request, "auctions/listing.html", context)
        else:
            context = {
                **context,
                "bid_count": listing.bids.count(),
                "user_has_highest_bid": user_has_highest_bid,
                "user_created_the_listing": listing.listed_by == request.user,
                "in_watchlist": request.user.watchlist.contains(listing),
                "comments": listing.comments.all().order_by("-date_created"),
                # I stored the form data of bid and comment forms in the session so this view can access
                # it when the bid and comment views redirect back to this view. 
                "bid_form": BidForm(request.session["bid_form"]) 
                    if request.session.get("bid_form") 
                    else BidForm(initial={"bidder": request.user, "listing": listing}),
                "comment_form": CommentForm(request.session["comment_form"]) 
                    if request.session.get("comment_form") 
                    else CommentForm(initial={"author": request.user, "listing": listing})
            }
            if request.session.get("bid_form") or request.session.get("comment_form"):
                request.session["bid_form"] = None
                request.session["comment_form"] = None
                return render(request, "auctions/listing.html", context, status=400)
            else:
                return render(request, "auctions/listing.html", context)
    else:
        if listing.status == "inactive":
            messages.add_message(request, messages.INFO, "Auction is closed.")
        return render(request, "auctions/listing.html", context)


@login_required
def my_listings(request):
    return render(request, "auctions/my_listings.html", {
        "listings": request.user.listings.all()
    })


@login_required()
def watchlist(request):
    if request.method == "POST":
        listing_id = request.POST["listing_id"]
        listing = Listing.objects.get(pk=listing_id)
        listing.watchers.add(request.user)
        messages.add_message(request, messages.SUCCESS, "Item added to watchlist!")
        return HttpResponseRedirect(reverse("listing", args=[listing_id]))
    else:
        return render(request, "auctions/watchlist.html", {
            "watchlist": request.user.watchlist.all()
        })


@login_required()
@require_POST
def delete_watchlist_item(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    request.user.watchlist.remove(listing)
    messages.add_message(request, messages.SUCCESS, "Item removed from watchlist!")
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))


@login_required()
@require_POST
def bid(request):
    form = BidForm(request.POST)
    if form.is_valid():
        bid = Bid.objects.create(**form.cleaned_data, bidder=request.user)
        bid.save()
        messages.add_message(request, messages.SUCCESS, "Bid placed successfully!")
    else:
        request.session["bid_form"] = request.POST
    return HttpResponseRedirect(reverse("listing", args=[request.POST["listing"]]))


@login_required()
@require_POST
def close_auction(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    if listing.listed_by != request.user:
        return JsonResponse({
            "message": "You can't close an auction listed by others!"
        }, status=403)
    else:
        listing.status = "inactive"
        listing.save()
        messages.add_message(request, messages.SUCCESS, "Auction has been closed!")
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))


@login_required()
@require_POST
def comment(request):
    if not Listing.objects.filter(pk=request.POST["listing"]).exists():
        return JsonResponse({
            "message": "You can't comment on a non-existing comment"
        }, status=404)
    else:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = Comment.objects.create(**form.cleaned_data, author=request.user)
            comment.save()
        else:
            request.session["comment_form"] = request.POST
        return HttpResponseRedirect(reverse("listing", args=[request.POST["listing"]]))


def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": [{
            **category.__dict__, 
            "item_count": category.listings.filter(status="active").count()
        } for category in Category.objects.all()]
    })


def listings_by_category(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return JsonResponse({
            "message": "A category with that ID does not exist!"
        }, status=404)
    category = Category.objects.get(pk=category_id)
    return render(request, "auctions/listings_by_category.html", {
        "listings": Listing.objects.filter(status="active",category=category),
        "category_name": category.name
    })







def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "registration/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "registration/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "registration/register.html")
