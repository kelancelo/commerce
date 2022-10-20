from django.urls import path

from . import views

# app_name = "auctions"
urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("watchlist/<int:listing_id>/delete", views.delete_watchlist_item, name="delete_watchlist_item"),
    path("bid", views.bid, name="bid"),
    path("listing/<int:listing_id>/close", views.close_auction, name="close_auction"),
    path("comment", views.comment, name="comment"),
    path("categories", views.categories, name="categories"),
    path("categories/<int:category_id>", views.listings_by_category, name="listings_by_category")
]
