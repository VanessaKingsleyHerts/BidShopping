from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
import time
import os

class TestHomePage(StaticLiveServerTestCase):

    # def setUp(self):
       # service = webdriver.ChromeService(executable_path='./functional_tests/chromedriver.exe')
       # self.browser = webdriver.Chrome(service=service)
    
    def setUp(self):
        # Configure ChromeOptions for headless CI
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # connect to the selenium/standalone-chrome service
        self.browser = webdriver.Remote(
            command_executor=os.environ["SELENIUM_REMOTE_URL"],
            options=options,
        )

    # def tearDown(self):
      #  self.browser.close()

    def tearDown(self):
        self.browser.quit()

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
        