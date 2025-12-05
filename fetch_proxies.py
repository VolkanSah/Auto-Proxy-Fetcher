import aiohttp
import asyncio
import logging
import random
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyFetcher:
    def __init__(self):
        self.proxies = set()

        # The list of sources is quite long, so I'm omitting it here for brevity 
        # but using your exact original list in the fixed code.
        self.sources = [
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/http.txt", "http"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks5.txt", "socks5"),
            #("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/http.txt", "http"),
            #("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/socks4.txt", "socks4"),
            #("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/socks5.txt", "socks5"),

            #("https://raw.githubusercontent.com/roosterkid/openproxylist/main/http.txt", "http"),
            #("https://raw.githubusercontent.com/roosterkid/openproxylist/main/socks4.txt", "socks4"),
            #("https://raw.githubusercontent.com/roosterkid/openproxylist/main/socks5.txt", "socks5"),

            # FIX: Corrected a typo in this URL, which had 'txt5' instead of 'txt'
            #("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt", "http"), 
            #("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks4.txt", "socks4"),
            #("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks5.txt", "socks5"),


           ]

    async def fetch_url(self, session, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; ProxyFetcher/1.0)"
            }
            timeout = aiohttp.ClientTimeout(total=15)

            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return await response.text()

                logger.warning(f"HTTP {response.status} for {url}")
                return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {type(e).__name__} - {e}")
            return None

    def parse_proxy_list(self, content, protocol):
        if not content:
            return

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                # Strip protocol prefix (http://, socks5://, etc)
                if "://" in line:
                    _, line = line.split("://", 1)

                # Remove authentication (user:pass@...)
                if "@" in line:
                    _, line = line.split("@", 1)

                parts = line.split(":")
                if len(parts) < 2:
                    continue

                host = parts[0].strip()
                port = parts[1].split("/")[0].split("#")[0].strip()

                if not port.isdigit():
                    continue

                port_int = int(port)
                if not (1 <= port_int <= 65535):
                    continue

                # Require at least something resembling hostnames or IPs
                if "." not in host and ":" not in host:
                    continue

                proxy_url = f"{protocol}://{host}:{port}"
                self.proxies.add(proxy_url)

            except Exception:
                continue  # Ignore malformed entries

    async def fetch_all_proxies(self):
        connector = aiohttp.TCPConnector(limit=30, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=20)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [self.fetch_url(session, url) for url, _ in self.sources]
            results = await asyncio.gather(*tasks)

            for (url, protocol), content in zip(self.sources, results):
                if content:
                    self.parse_proxy_list(content, protocol)
                else:
                    logger.warning(f"Skipped parsing for {url} (empty/no content)")

    def save_proxies(self):
        if not self.proxies:
            logger.warning("No proxies found to save!")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert the set to a list to allow shuffling.
        proxy_list = list(self.proxies) 
        # Shuffle the list in-place.
        random.shuffle(proxy_list) 

        # Save metadata
        with open("info.txt", "w", encoding="utf-8") as f:
            f.write("# High-Quality Proxy List\n")
            f.write(f"# Updated: {timestamp}\n")
            f.write(f"# Total unique proxies: {len(proxy_list)}\n") # Use proxy_list length
            f.write(f"# Sources: {len(self.sources)} URLs\n\n")

            f.write("# Sources used:\n")
            for url, protocol in self.sources:
                f.write(f"#   [{protocol.upper()}] {url}\n")

        # Save proxies - FIX APPLIED HERE
        with open("proxies.txt", "w", encoding="utf-8") as f:
            # Iterate over the shuffled list
            for proxy in proxy_list: 
                f.write(proxy + "\n")

        logger.info(f"Saved {len(proxy_list)} unique proxies to proxies.txt")


async def main():
    fetcher = ProxyFetcher()
    logger.info("Starting proxy fetch...")
    await fetcher.fetch_all_proxies()
    fetcher.save_proxies()


if __name__ == "__main__":
    asyncio.run(main())
