import aiohttp
import asyncio
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyFetcher:
    def __init__(self):

        self.proxies = set()

        # DEFAULT sources (HTTP only)
        self.sources = [
            ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "http"),
            ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt", "http"),
        ]

        # CUSTOM GitHub-token-protected sources (automatic protocol)
        self.sources += [
            # YOUTUBE
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/refs/heads/main/custom/youtube/socks5.txt", "socks5"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/refs/heads/main/custom/youtube/http.txt",   "http"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/refs/heads/main/custom/youtube/socks4.txt", "socks4"),

            # INSTAGRAM
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/refs/heads/main/custom/instagram/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/refs/heads/main/custom/instagram/socks5.txt", "socks5"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/refs/heads/main/custom/instagram/http.txt",   "http"),
        ]


    async def fetch_url(self, session, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
            }

            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    return await response.text()

                logger.warning(f"Failed to fetch {url}: Status {response.status}")
                return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None


    def parse_proxy_list(self, content, protocol):
        if not content:
            return

        for line in content.split("\n"):
            line = line.strip()
            if ":" not in line:
                continue

            try:
                host, port = line.split(":")[:2]

                if port.isdigit() and 1 <= int(port) <= 65535:
                    self.proxies.add(f"{protocol}://{host}:{port}")

            except:
                continue


    async def fetch_all_proxies(self):
        async with aiohttp.ClientSession() as session:

            tasks = [
                self.fetch_url(session, url)
                for url, _protocol in self.sources
            ]

            results = await asyncio.gather(*tasks)

            for (url, protocol), content in zip(self.sources, results):
                if content:
                    self.parse_proxy_list(content, protocol)


    def save_proxies(self):
        if not self.proxies:
            logger.warning("No proxies found to save!")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open("info.txt", "w") as f:
            f.write(f"# Unified Proxy List - Updated: {timestamp}\n")
            f.write(f"# Total proxies: {len(self.proxies)}\n")
            f.write(f"# Merged from {len(self.sources)} sources\n\n")
        with open("proxies.txt", "w") as ff:
            for proxy in self.proxies:
                ff.write(proxy + "\n")

        logger.info(f"Saved {len(self.proxies)} unified proxies to proxies.txt")


async def main():
    fetcher = ProxyFetcher()
    await fetcher.fetch_all_proxies()
    fetcher.save_proxies()


if __name__ == "__main__":
    asyncio.run(main())
