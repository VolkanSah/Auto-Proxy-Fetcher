import aiohttp
import asyncio
import logging
import random
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyFetcher:
    def __init__(self):
        self.proxies = {
            "youtube": set(),
            "google": set(),
            "discord": set(),
            "instagram": set(),
            "misc": set(),
        }

        # Define all proxy sources by category
        self.sources = [
            # YouTube
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/http.txt", "http", "youtube"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks4.txt", "socks4", "youtube"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks5.txt", "socks5", "youtube"),

            # Google
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/google/http.txt", "http", "google"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/google/socks4.txt", "socks4", "google"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/google/socks5.txt", "socks5", "google"),

            # Discord
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/discord/http.txt", "http", "discord"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/discord/socks4.txt", "socks4", "discord"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/discord/socks5.txt", "socks5", "discord"),

            # Instagram
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/http.txt", "http", "instagram"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/socks4.txt", "socks4", "instagram"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/socks5.txt", "socks5", "instagram"),

            # Miscellaneous (Monosans)
            ("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt", "http", "misc"),
            ("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks4.txt", "socks4", "misc"),
            ("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks5.txt", "socks5", "misc"),
            ("https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/HTTPS_RAW.txt", "http", "misc"),
            ("https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/SOCKS4_RAW.txt", "socks4", "misc"),
                        ("https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/SOCKS5_RAW.txt", "socks5", "misc"),
        ]

    async def fetch_url(self, session, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; ProxyFetcher/1.0)"}
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

    def parse_proxy_list(self, content, protocol, category):
        if not content:
            return
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                if "://" in line:
                    _, line = line.split("://", 1)
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

                if "." not in host and ":" not in host:
                    continue

                proxy_url = f"{protocol}://{host}:{port}"
                self.proxies[category].add(proxy_url)
            except Exception:
                continue

    async def fetch_all_proxies(self):
        connector = aiohttp.TCPConnector(limit=30, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=20)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [self.fetch_url(session, url) for url, _, _ in self.sources]
            results = await asyncio.gather(*tasks)

            for (url, protocol, category), content in zip(self.sources, results):
                if content:
                    self.parse_proxy_list(content, protocol, category)
                else:
                    logger.warning(f"Skipped parsing for {url} (empty/no content)")

    def save_proxies(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_proxies = sum(len(v) for v in self.proxies.values())

        # Save info.txt metadata
        with open("info.txt", "w", encoding="utf-8") as f:
            f.write("# High-Quality Proxy List\n")
            f.write(f"# Updated: {timestamp}\n")
            f.write(f"# Total unique proxies: {total_proxies}\n")
            f.write(f"# Sources: {len(self.sources)} URLs\n\n")
            f.write("# Sources used:\n")
            for url, protocol, category in self.sources:
                f.write(f"#   [{category.upper()} | {protocol.upper()}] {url}\n")

        # Save per-category proxy files
        for category, proxy_set in self.proxies.items():
            if not proxy_set:
                logger.warning(f"No {category} proxies found to save.")
                continue

            proxy_list = list(proxy_set)
            random.shuffle(proxy_list)
            filename = f"{category}_proxies.txt"

            with open(filename, "w", encoding="utf-8") as f:
                for proxy in proxy_list:
                    f.write(proxy + "\n")

            logger.info(f"Saved {len(proxy_list)} {category} proxies to {filename}")


async def main():
    fetcher = ProxyFetcher()
    logger.info("Starting proxy fetch...")
    await fetcher.fetch_all_proxies()
    fetcher.save_proxies()


if __name__ == "__main__":
    asyncio.run(main())
