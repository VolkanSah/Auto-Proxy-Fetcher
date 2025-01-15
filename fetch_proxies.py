import aiohttp
import asyncio
from datetime import datetime
import ssl
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyFetcher:
    def __init__(self):
        self.proxies = set()
        self.valid_proxies = set()
        self.sources = [
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
            'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt',
            'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
            'https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt',
            'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://www.proxy-list.download/api/v1/get?type=https'
        ]

    async def fetch_url(self, session, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    return await response.text()
                logger.warning(f"Failed to fetch {url}: Status {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def parse_proxy_list(self, content, url):
        if not content:
            return
        try:
            # Special handling for JSON APIs
            if 'api' in url:
                if 'geonode' in url:
                    import json
                    data = json.loads(content)
                    for item in data.get('data', []):
                        proxy = f"{item.get('ip')}:{item.get('port')}"
                        self.proxies.add(proxy)
                    return
            # Standard line-based parsing
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and ':' in line:
                    try:
                        proxy = line.split()[0] if ' ' in line else line
                        host, port = proxy.split(':')[:2]
                        if host and port.isdigit() and 1 <= int(port) <= 65535:
                            self.proxies.add(f"{host}:{port}")
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {str(e)}")

    async def check_proxy(self, session, proxy):
        try:
            proxy_url = f"http://{proxy}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with session.get('http://httpbin.org/ip', proxy=proxy_url, headers=headers, timeout=60) as response:
                if response.status == 200:
                    self.valid_proxies.add(proxy)
                    logger.info(f"Proxy {proxy} is working.")
                else:
                    logger.warning(f"Proxy {proxy} failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Error checking proxy {proxy}: {str(e)}")

    async def fetch_all_proxies(self):
        # Create a custom SSL context to disable certificate verification (similar to rejectUnauthorized: false)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Use the custom SSL context in the aiohttp session
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            tasks = [self.fetch_url(session, url) for url in self.sources]
            results = await asyncio.gather(*tasks)
            
            for url, content in zip(self.sources, results):
                if content:
                    self.parse_proxy_list(content, url)

            # Check each proxy for validity
            check_tasks = [self.check_proxy(session, proxy) for proxy in self.proxies]
            await asyncio.gather(*check_tasks)

    def save_proxies(self):
        if not self.valid_proxies:
            logger.warning("No valid proxies found to save!")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('proxies.txt', 'w') as f:
            f.write(f"# Proxy List - Updated: {timestamp}\n")
            f.write(f"# Total valid proxies: {len(self.valid_proxies)}\n")
            f.write(f"# Sources used: {len(self.sources)}\n\n")

            # Save only valid proxies
            for proxy in sorted(self.valid_proxies):
                f.write(f"{proxy}\n")
        
        logger.info(f"Saved {len(self.valid_proxies)} valid proxies to proxies.txt")

async def main():
    fetcher = ProxyFetcher()
    await fetcher.fetch_all_proxies()
    fetcher.save_proxies()

if __name__ == "__main__":
    asyncio.run(main())
