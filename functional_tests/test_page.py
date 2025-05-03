from unittest import skip
import os
import traceback
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from selenium import webdriver
from django.urls import reverse
import time
from urllib.parse import urlparse

SCREENSHOT_DIR = os.path.join(os.getcwd(), 'functional_tests', 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

@tag('functional')
class TestHomePage(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.browser = webdriver.Chrome(options=options)
        cls.remote_server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def test_home(self):
        self.browser.get(self.remote_server_url)
        time.sleep(1)

    def test_user_login(self):
        url = self.remote_server_url + reverse('login_user')
        self.browser.get(url)
        time.sleep(1)

    def test_admin_login(self):
        url = self.remote_server_url + reverse('login_admin')
        self.browser.get(url)
        time.sleep(1)

    def test_about(self):
        url = self.remote_server_url + reverse('about')
        self.browser.get(url)
        time.sleep(1)

    def test_contact(self):
        url = self.remote_server_url + reverse('contact')
        self.browser.get(url)
        time.sleep(1)

    def test_file_upload(self):
        self.browser.get(self.remote_server_url + reverse('upload_view'))
        upload_input = self.browser.find_element("name", "file_field")
        upload_input.send_keys(os.path.join(os.getcwd(), 'functional_tests', 'fixtures', 'sample.pdf'))
        self.browser.find_element("css selector", 'button[type=submit]').click()
        success = self.browser.find_element("id", "upload-success")
        self.assertIn('uploaded', success.text.lower())

    def test_file_download_link(self):
        self.browser.get(self.remote_server_url + reverse('download_view'))
        time.sleep(2)
        link = self.browser.find_element("tag name", "a")
        href = link.get_attribute('href')
        import requests
        r = requests.get(href)
        self.assertEqual(r.headers['Content-Type'], 'application/pdf')
        self.assertGreater(len(r.content), 0)
