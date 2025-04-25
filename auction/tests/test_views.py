from unittest import skip
from django.test import Client, TransactionTestCase
from django.urls import reverse
from auction.models import Product, Aucted_Product, User, Member, Status

class TestUrls(TransactionTestCase):

    def setUp(self):
        self.client = Client()
        status = Status.objects.create(status="Accepted")
        pro1=Product.objects.create(id=0,status=status)
        self.user = User.objects.create_user(username="user1", password="user1")
        seller = Member.objects.create(user=self.user)
        Aucted_Product.objects.create(product=pro1,user=seller)

    def test_home_GET(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'carousel.html')

    def test_login_user_GET(self):
        response = self.client.get(reverse('login_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_user_POST(self):
        response = self.client.post(reverse('login_user'), {
            'uname': 'user1',
            'pwd': 'user1'
        })
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(self.user)
        self.assertTemplateUsed(response, 'login.html')

    @skip
    def test_view_auction_GET(self):
        response = self.client.get(reverse('view_auction', args=[0]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_auction.html')

    def test_get_latest_auctions_GET(self):
        response = self.client.get(reverse('get_latest_auctions', args=[0]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    