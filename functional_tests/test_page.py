import os, socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
import time

class TestHomePage(StaticLiveServerTestCase):
    # ensure Django binds 0.0.0.0
    host = "0.0.0.0"  

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # figure out this container's IP on the Docker network
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        # point tests at that IP+port instead of "localhost"
        cls.remote_server_url = f"http://{ip}:{cls.server_thread.port}"

        # configure headless Chrome
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        # point at the Selenium service
        self_url = os.environ["SELENIUM_REMOTE_URL"]
        cls.browser = webdriver.Remote(
            command_executor=self_url,
            options=opts
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def test_home(self):
        self.browser.get(self.remote_server_url)
        time.sleep(1)

    def test_user_login(self):
        url = self.remote_server_url + reverse("login_user")
        self.browser.get(url)
        time.sleep(1)

    def test_admin_login(self):
        url = self.remote_server_url + reverse("login_admin")
        self.browser.get(url)
        time.sleep(1)

    def test_about(self):
        url = self.remote_server_url + reverse("about")
        self.browser.get(url)
        time.sleep(1)

    def test_contact(self):
        url = self.remote_server_url + reverse("contact")
        self.browser.get(url)
        time.sleep(1)
