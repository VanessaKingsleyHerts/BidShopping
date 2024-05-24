from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
import time

class TestHomePage(StaticLiveServerTestCase):

    def setUp(self):
        service = webdriver.ChromeService(executable_path='./functional_tests/chromedriver.exe')
        self.browser = webdriver.Chrome(service=service)
        

    def tearDown(self):
        self.browser.close()

    def test_home(self):
        self.browser.get(self.live_server_url)
        time.sleep(2)

    def test_user_login(self):
        url = self.live_server_url + reverse('login_user')
        self.browser.get(url)
        time.sleep(2)

    def test_admin_login(self):
        url = self.live_server_url + reverse('login_admin')
        self.browser.get(url)
        time.sleep(2)

    def test_about(self):
        url = self.live_server_url + reverse('about')
        self.browser.get(url)
        time.sleep(2)

    def test_admin_login(self):
        url = self.live_server_url + reverse('contact')
        self.browser.get(url)
        time.sleep(2)