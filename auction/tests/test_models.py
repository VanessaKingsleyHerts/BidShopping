from unittest import skip
from django.test import Client, TransactionTestCase
from django.urls import reverse
from auction.models import Product, Aucted_Product, User, Member, Status

class TestModels(TransactionTestCase):

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

    