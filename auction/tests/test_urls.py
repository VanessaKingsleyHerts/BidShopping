from django.test import SimpleTestCase
from django.urls import reverse, resolve
from auction.views import Home, Member_Home, view_auction

class TestUrls(SimpleTestCase):

    def test_home(self):
        url = reverse('home')
        #print(resolve(url))
        self.assertEqual(resolve(url).func, Home)

    def test_user_home(self):
        url = reverse('user_home')
        #print(resolve(url))
        self.assertEqual(resolve(url).func, Member_Home)

    def test_view_auction(self):
        url = reverse('view_auction', args=[0])
        #print(resolve(url))
        self.assertEqual(resolve(url).func, view_auction)