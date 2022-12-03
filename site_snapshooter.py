import argparse
import os
import sys
from datetime import datetime
from time import sleep
from typing import List
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import xmltodict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

local_dir = os.path.dirname(__file__)
generated_resources_dir = os.path.join(local_dir, 'generated_resources')
os.makedirs(generated_resources_dir, exist_ok=True)


class SiteSnapshooter:
    sleep_time = 5

    def __init__(self, sitemap_path, accept_cookie_element_id=None, headless=False):
        self.links = []
        self.sitemap = self.read_sitemap(sitemap_path)
        self.accept_cookie_element_id = accept_cookie_element_id
        self.headless = headless
        self.urls = self.get_urls_from_sitemap(self.sitemap)
        self.base_url = urlparse(self.urls[0]).netloc
        self.site_resource_dir = os.path.join(generated_resources_dir, self.base_url)
        self.snapshot_dir = os.path.join(self.site_resource_dir,
                                         f'snapshot_{datetime.now().strftime("%Y_%m_%d__%H_%M_%S")}')
        self.html_content_dir = os.path.join(self.snapshot_dir, 'html_content')
        self.screenshots_dir = os.path.join(self.snapshot_dir, 'screenshots')
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.html_content_dir, exist_ok=True)

    @staticmethod
    def read_sitemap(sitemap_path: str) -> dict:
        with open(sitemap_path, 'r') as f:
            return xmltodict.parse(f.read())

    @staticmethod
    def get_urls_from_sitemap(sitemap: dict) -> list:
        urls = []
        for url in sitemap['urlset']['url']:
            urls.append(url['loc'])
        return urls

    @staticmethod
    def is_valid_uri(uri: str) -> bool:
        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def get_html_content(self, urls: List[str]) -> None:
        for index, url in enumerate(urls):
            print(f"Getting HTML content from {url}")
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/39.0.2171.95 Safari/537.36'})
            try:
                html = urlopen(req).read()
                page_dir_name = self.get_page_dir_name(url)
                with open(os.path.join(self.html_content_dir, f'{page_dir_name}.html'), 'wb') as f:
                    f.write(html)
            except HTTPError:
                print(f"Error getting links from {url}")
                continue
            self.print_progress_bar(index, len(urls), "HTML content processed")

    def get_pages_screenshots(self, urls: List[str]) -> None:
        parsed_url = urlparse(urls[0])
        base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
        options = Options()
        options.headless = self.headless
        options.add_argument("--disable-notifications")
        options.add_argument("disable-infobars")
        driver = webdriver.Chrome(options=options)
        driver.get(base_url)

        if self.accept_cookie_element_id:
            print("Accepting cookies. Clicking on element with id: {}".format(self.accept_cookie_element_id))
            WebDriverWait(driver, self.sleep_time).until(
                EC.element_to_be_clickable((By.ID, self.accept_cookie_element_id))).click()

        sleep(self.sleep_time)  # wait for page to load completely and/or accept cookies
        driver.set_window_size(1920, 1080)
        for index, url in enumerate(urls):
            print(f"Getting page screenshot from {url}")
            driver.get(url)
            if self.headless:
                max_width = driver.execute_script('return document.documentElement.scrollWidth')
                max_height = driver.execute_script('return document.documentElement.scrollHeight')
                driver.set_window_size(max_width, max_height)
            else:
                driver.fullscreen_window()

            page_dir_name = self.get_page_dir_name(url)
            driver.save_screenshot(f"{self.screenshots_dir}/{page_dir_name}.png")
            self.print_progress_bar(index, len(urls), "Page screenshot processed")
        driver.quit()

    @staticmethod
    def get_page_dir_name(page_url: str) -> str:
        return urlparse(page_url).path.replace('/', '_')

    def generate_snapshot(self) -> None:
        self.get_html_content(self.urls)
        self.get_pages_screenshots(self.urls)

    @staticmethod
    def print_progress_bar(index: int, total: int, label: str) -> None:
        bar_width = 50
        progress = index / total
        sys.stdout.write('\r')
        sys.stdout.write(f"[{'=' * int(bar_width * progress):{bar_width}s}] {int(100 * progress)}%  {label}")
        sys.stdout.write('\n')
        sys.stdout.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create snapshot for a website')
    parser.add_argument('sitemap', type=str, help='The sitemap of the website in xml format')
    parser.add_argument('--cookie_id', '-c', type=str, help='The id of the clickable element to accept cookies',
                        default=None)
    parser.add_argument('--headless', '-q', help='Run the script in headless mode', action='store_true', default=False)
    args = parser.parse_args()

    snapshooter = SiteSnapshooter(args.sitemap, args.cookie_id, args.headless)
    snapshooter.generate_snapshot()
    print('Done. Check the results in the generated_resources folder')
