import os
import traceback
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from django.urls import reverse
import time

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

        # connect to the selenium/standalone-chrome service
        cls.browser = webdriver.Remote(
            command_executor=os.environ["SELENIUM_REMOTE_URL"],
            options=options,
        )
        cls.remote_server_url = cls.live_server_url


    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def tearDown(self):
        # if the test just errored, save screenshot
        for method, error in self._outcome.errors:
            if error:
                name = self._testMethodName
                path = os.path.join(SCREENSHOT_DIR, f'{name}.png')
                try:
                    self.browser.save_screenshot(path)
                except WebDriverException:
                    pass
        super().tearDown()

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

    def test_file_upload(self):
        self.browser.get(self.live_server_url + reverse('upload_view'))
        upload_input = self.browser.find_element_by_name('file_field')
        # ensure you have a sample file in your repo
        upload_input.send_keys(os.path.join(os.getcwd(), 'functional_tests', 'fixtures', 'sample.pdf'))
        self.browser.find_element_by_css_selector('button[type=submit]').click()
        # assert the success message or download link appears
        success = self.browser.find_element_by_id('upload-success')
        self.assertIn('uploaded', success.text.lower())

    def test_file_download_link(self):
        self.browser.get(self.live_server_url + reverse('download_view'))
        link = self.browser.find_element_by_tag_name('a')
        href = link.get_attribute('href')
        # you could issue a direct HTTP GET here to validate headers:
        import requests
        r = requests.get(href)
        self.assertEqual(r.headers['Content-Type'], 'application/pdf')
        self.assertGreater(len(r.content), 0)

