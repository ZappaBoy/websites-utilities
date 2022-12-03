import argparse
import os
import re
import sys
from datetime import datetime
from typing import List
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import xmltodict
from bs4 import BeautifulSoup

local_dir = os.path.dirname(__file__)
generated_resources_dir = os.path.join(local_dir, 'generated_resources')
os.makedirs(generated_resources_dir, exist_ok=True)


class SiteMapper:
    match_href_regex = r"(?<=href=\\\")(http://|https://|/)([^\\\"#?]*((?=\.)(\.htm|\.html|\.asp|\.aspx|\.cgi|\.pl|\.js|\.jsp|\.php|\.xhtml/)|(?=/)/[^\\\"/#?\s\.]+))"
    match_url_regex = r"(^http://|^https://|^/)(.*((?=\.)(\.htm|\.html|\.asp|\.aspx|\.cgi|\.pl|\.js|\.jsp|\.php|\.xhtml|.+/)$|(?=/)/[^\\\"/#?\s\.]+))"
    match_href = re.compile(match_href_regex, re.MULTILINE | re.IGNORECASE)
    match_url = re.compile(match_url_regex, re.MULTILINE | re.IGNORECASE)

    def __init__(self, url):
        self.url = url
        self.links = []
        self.sitemap = []
        self.base_url = self.extract_base_url(url)
        parsed_url = urlparse(self.base_url)
        self.sitemaps_resources_dir = os.path.join(generated_resources_dir, parsed_url.netloc)
        os.makedirs(self.sitemaps_resources_dir, exist_ok=True)

    @staticmethod
    def is_valid_uri(uri: str) -> bool:
        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def has_same_base_url(self, url: str) -> bool:
        return self.extract_base_url(url) == self.base_url

    @staticmethod
    def extract_base_url(url: str) -> str:
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    def get_complete_url(self, url: str) -> str:
        if url.startswith('/') and not url.startswith('//'):
            return f"{self.base_url}{url}"
        url = url.encode('ascii', 'ignore').decode('ascii')
        return url if self.is_valid_uri(url) else ''

    def get_links(self, url: str) -> None:
        print(f"Getting links from {url}")
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/39.0.2171.95 Safari/537.36'})
        try:
            source_code = urlopen(req).read()
        except HTTPError:
            print(f"Error getting links from {url}")
            return

        self.parse_source_code(source_code.decode('utf-8'))

        soup = BeautifulSoup(source_code, features="html.parser", from_encoding="iso-8859-1")
        self.parse_rendered_html(soup)

    def parse_source_code(self, source_code: str) -> None:
        for url in self.match_href.findall(source_code):
            href_url = ''.join(url)
            self.check_and_add_link(href_url)

    def parse_rendered_html(self, soup: BeautifulSoup) -> None:
        for link in soup.find_all('a', href=True):
            href_url: str = link.get('href')
            href_match = self.match_url.match(href_url)
            if not href_match:
                continue
            else:
                href_url = href_match.group()
            self.check_and_add_link(href_url)

    def check_and_add_link(self, link: str) -> None:
        complete_url = self.get_complete_url(link)
        if self.has_same_base_url(complete_url) and complete_url not in self.links:
            self.links.append(complete_url)

    def generate_sitemap(self) -> None:
        self.get_links(self.url)
        self.links.append(self.url)

        i = 0
        while i < len(self.links):
            self.get_links(self.links[i])
            i += 1
            self.print_progress_bar(i, len(self.links), "Links processed")
        self.create_sitemap()

    @staticmethod
    def print_progress_bar(index: int, total: int, label: str) -> None:
        bar_width = 50
        progress = index / total
        sys.stdout.write('\r')
        sys.stdout.write(f"[{'=' * int(bar_width * progress):{bar_width}s}] {int(100 * progress)}%  {label}")
        sys.stdout.write('\n')
        sys.stdout.flush()

    @staticmethod
    def calculate_priority(url: str) -> float:
        priority = 1.00
        url = urlparse(url)
        occurrences = url.path.count('/')
        return priority - (0.1 * (occurrences - 1))

    def create_sitemap(self) -> None:
        urls = []
        now = datetime.now()
        for link in self.links:
            urls.append({
                'loc': link,
                'lastmod': now.isoformat(),
                'changefreq': 'daily',
                'priority': self.calculate_priority(link)
            })
        self.sitemap = {
            'urlset': {
                '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                '@xsi:schemaLocation': 'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd',
                'url': urls
            }
        }
        xml_sitemap = xmltodict.unparse(self.sitemap, pretty=True)
        sitemap_path = os.path.join(self.sitemaps_resources_dir, f'sitemap.xml')
        with open(sitemap_path, 'w') as f:
            f.write(xml_sitemap)

    def get_sitemap(self) -> List[dict]:
        return self.sitemap


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create sitemap for a website')
    parser.add_argument('url', type=str, help='The base url of the website. Example: https://www.example.com')
    args = parser.parse_args()

    base_url = args.url
    site_mapper = SiteMapper(base_url)
    site_mapper.generate_sitemap()
    print('Done. Check the results in the generated_resources folder')
