from django.test import TestCase, Client
from .models import *
from django.urls import reverse
from .forms import *


def create_test_data(cls):
    # Create Users.
    cls.u1 = User.objects.create_user("username1", "email1", "password1")
    cls.u2 = User.objects.create_user("username2", "email2", "password2")
    cls.u1.save()
    cls.u2.save()
    # Create Categories
    cls.c1 = Category.objects.create(name="Instruments")
    cls.c2 = Category.objects.create(name="Accessories")
    # Create Listings
    cls.l1 = Listing.objects.create(
        title = "Schecter Zacky V",
        description = "You know",
        starting_bid = 600,
        listed_by = cls.u1,
        category = cls.c1
    )
    cls.l2 = Listing.objects.create(
        title = "Bullet Bracelet",
        description = "Bracelet made with bullet",
        starting_bid = 100,
        listed_by = cls.u2,
        category = cls.c2
    )
    cls.l3 = Listing.objects.create(
        title = "Death Note",
        description = "awawawa",
        starting_bid = 50,
        listed_by = cls.u2,
        category = cls.c2,
        status="inactive"
    )
    # Create Bids
    cls.b1 = Bid.objects.create(bidder=cls.u1, listing=cls.l1, price=600)
    cls.b2 = Bid.objects.create(bidder=cls.u2, listing=cls.l1, price=610)
    # Create Comments
    cls.comment1 = Comment.objects.create(author=cls.u1, listing=cls.l2, text="test comment 1")
    cls.comment2 = Comment.objects.create(author=cls.u2, listing=cls.l2, text="test comment 2")
    # Create Watchlist
    cls.u1.watchlist.add(cls.l1)
    # Create authenticated client.
    cls.client1 = Client()
    cls.client1.login(username="username1", password="password1")
    # Create unauthenticated client.
    cls.client2 = Client()


class ListingModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_get_current_price_with_bids(self):
        self.assertEqual(self.l1.get_current_price(), 610)     

    def test_get_current_price_without_bids(self):
        self.assertEqual(self.l2.get_current_price(), 100)


class IndexViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_get_request(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listings"].count(), 3)


class ActiveListingsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_get_request(self):
        response = self.client.get(reverse("active_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listings"].count(), 2)


class MyListingsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_unauthenticated_get_request(self):
        response = MyListingsViewTest.client2.get(reverse("my_listings"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("my_listings"))

    def test_authenticated_get_request(self):
        response = MyListingsViewTest.client1.get(reverse("my_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listings"].count(), 1)


class CreateListingViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_unauthenticated_get_request(self):
        response = CreateListingViewTest.client2.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("create_listing"))


    def test_authenticated_get_request(self):
        response = CreateListingViewTest.client1.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.context["form"], ListingForm))

    def test_valid_post_request(self):
        response = CreateListingViewTest.client1.post(reverse("create_listing"), {
            "title": "Test Listing",
            "description": "Test Listing Description",
            "starting_bid": 69
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_post_request(self):
        response = CreateListingViewTest.client1.post(reverse("create_listing"), {
            "title": "Test Listing",
            "description": "Test Listing Description"
        })
        self.assertEqual(response.status_code, 400)


class ListingViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_unauthenticated_get_request(self):
        response = ListingViewTest.client2.get(reverse("listing", args=[ListingViewTest.l1.id]))
        expected_context = ["listing", "current_price"]
        returned_context = response.context.keys()
        self.assertTrue(all(context in returned_context for context in expected_context))

    def test_authenticated_get_request(self):
        response = ListingViewTest.client1.get(reverse("listing", args=[ListingViewTest.l1.id]))
        expected_context = [
            "listing", 
            "current_price", 
            "bid_count", 
            "user_has_highest_bid",
            "user_created_the_listing",
            "in_watchlist",
            "comments",
            "bid_form",
            "comment_form"
        ]
        returned_context = response.context.keys()
        self.assertTrue(all(context in returned_context for context in expected_context))
        self.assertEqual(response.context["listing"], ListingViewTest.l1)
        self.assertEqual(response.context["current_price"], 610)
        self.assertEqual(response.context["bid_count"], 2)
        self.assertFalse(response.context["user_has_highest_bid"])
        self.assertTrue(response.context["user_created_the_listing"])
        self.assertTrue(response.context["in_watchlist"])
        self.assertEqual(response.context["comments"].count(), 0)
        self.assertTrue(isinstance(response.context["bid_form"], BidForm))
        self.assertTrue(isinstance(response.context["comment_form"], CommentForm))


class WatchlistViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_unauthenticated_get_request(self):
        response = WatchlistViewTest.client2.get(reverse("watchlist"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("watchlist"))


    def test_authenticated_get_request(self):
        response = WatchlistViewTest.client1.get(reverse("watchlist"))
        self.assertEqual(response.context["watchlist"].count(), 1)

    def test_post_request(self):
        response = WatchlistViewTest.client1.post(
            reverse("watchlist"), 
            {"listing_id": WatchlistViewTest.l2.id}
        )
        self.assertRedirects(response, reverse("listing", args=[WatchlistViewTest.l2.id]))


class DeleteWatchlistItemViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_unauthenticated_request(self):
        response = DeleteWatchlistItemViewTest.client2.post(reverse(
            "delete_watchlist_item", 
            args=[DeleteWatchlistItemViewTest.l1.id]
        ))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, 
            reverse("login") + "?next=" + reverse(
                "delete_watchlist_item", 
                args=[DeleteWatchlistItemViewTest.l1.id]
            )
        )

    def test_authenticated_request(self):
        response = DeleteWatchlistItemViewTest.client1.post(
            reverse("delete_watchlist_item", args=[DeleteWatchlistItemViewTest.l1.id]) 
        )
        self.assertRedirects(response, reverse("listing", args=[DeleteWatchlistItemViewTest.l1.id]))

    
class BidViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_unauthenticated_request(self):
        response = BidViewTest.client2.post(
            reverse("bid"), 
            {"listing": BidViewTest.l2.id, "price": 100}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, 
            reverse("login") + "?next=" + reverse("bid")
        )

    def test_valid_request(self):
        response = BidViewTest.client1.post(
            reverse("bid"), 
            {"listing": BidViewTest.l2.id, "price": 100}
        )
        self.assertRedirects(
            response, 
            reverse("listing", args=[BidViewTest.l2.id]), 
            target_status_code=200
        )

    def test_invalid_request(self):
        response = BidViewTest.client1.post(
            reverse("bid"), 
            {"listing": BidViewTest.l2.id, "price": 99}
        )
        self.assertRedirects(
            response, 
            reverse("listing", args=[BidViewTest.l2.id]), 
            target_status_code=400
        )


class CloseAuctionViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)
    
    def test_unauthenticated_request(self):
        response = CloseAuctionViewTest.client2.post(reverse(
            "close_auction", 
            args=[CloseAuctionViewTest.l2.id]
        ))
        self.assertRedirects(
            response, 
            reverse("login") + "?next=" + reverse("close_auction", args=[CloseAuctionViewTest.l2.id])
        )

    def test_authenticated_request(self):
        response = CloseAuctionViewTest.client1.post(reverse(
            "close_auction", 
            args=[CloseAuctionViewTest.l1.id]
        ))
        self.assertRedirects(
            response,
            reverse("listing", args=[CloseAuctionViewTest.l1.id])
        )

    def test_close_other_users_listing(self):
        response = CloseAuctionViewTest.client1.post(reverse(
            "close_auction", 
            args=[CloseAuctionViewTest.l2.id]
        ))
        self.assertEqual(response.status_code, 403)
        

class CommentViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)
    
    def test_unauthenticated_request(self):
        response = CommentViewTest.client2.post(
            reverse("comment"),
            {"listing": CommentViewTest.l1.id, "text": "test comment"}
        )
        self.assertRedirects(
            response, 
            reverse("login") + "?next=" + reverse("comment")
        )

    def test_valid_comment(self):
        response = CommentViewTest.client1.post(
            reverse("comment"),
            {"listing": CommentViewTest.l1.id, "text": "test comment"}
        )
        self.assertRedirects(
            response,
            reverse("listing", args=[CommentViewTest.l1.id]),
            target_status_code=200
        )

    def test_create_comment_without_text(self):
        response = CommentViewTest.client1.post(
            reverse("comment"),
            {"listing": CommentViewTest.l1.id, "text": ""}
        )
        self.assertRedirects(
            response,
            reverse("listing", args=[CommentViewTest.l1.id]),
            target_status_code=400
        )

    def test_create_comment_on_nonexisting_listing(self):
        response = CommentViewTest.client1.post(
            reverse("comment"),
            {"listing": 4, "text": "test comment"}
        )
        self.assertEqual(response.status_code, 404)


class CategoriesViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_get_request(self):
        response = CategoriesViewTest.client2.get(reverse("categories"))
        self.assertEqual(len(response.context["categories"]), 2)


class ListingsByCategoryViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data(cls)

    def test_request_with_valid_category(self):
        response = ListingsByCategoryViewTest.client2.get(reverse(
            "listings_by_category",
            args=[ListingsByCategoryViewTest.c1.id]
        ))
        self.assertEqual(response.context["listings"].count(), 1)
        self.assertEqual(response.context["category_name"], "Instruments")

    def test_request_with_invalid_category(self):
        response = ListingsByCategoryViewTest.client2.get(reverse(
            "listings_by_category",
            args=[3]
        ))
        self.assertEqual(response.status_code, 404)