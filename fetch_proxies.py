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

        self.sources = [
            # original sources
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/http.txt", "http"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks5.txt", "socks5"),
            ("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt", "http"),
            ("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/socks5.txt", "socks5"),

            ("https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt", "socks5"),


        ]

    async def fetch_url(self, session, url):
        try:
            headers = { "User-Agent": "Mozilla/5.0 (compatible; ProxyFetcher/1.0)" }
            timeout = aiohttp.ClientTimeout(total=15)
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 200:
                    return await resp.text()
                logger.warning(f"HTTP {resp.status} for {url}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
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
            if "://" in line:
                _, line = line.split("://",1)
            if "@" in line:
                _, line = line.split("@",1)

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

            proxy_url = f"{protocol}://{host}:{port_int}"
            self.proxies.add(proxy_url)

    async def fetch_all_proxies(self):
        connector = aiohttp.TCPConnector(limit=30, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [ self.fetch_url(session, url) for url, _ in self.sources ]
            results = await asyncio.gather(*tasks)
            for (url, proto), content in zip(self.sources, results):
                if content:
                    self.parse_proxy_list(content, proto)
                else:
                    logger.warning(f"Skipped {url} (no content)")

    def save_proxies(self, proxy_file="proxies.txt", info_file="info.txt"):
        if not self.proxies:
            logger.warning("No proxies collected.")
            return
        proxy_list = list(self.proxies)
        random.shuffle(proxy_list)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(info_file, "w", encoding="utf-8") as f:
            f.write(f"# Proxy list updated: {now}\n")
            f.write(f"# Total unique proxies: {len(proxy_list)}\n")
            f.write("# Sources:\n")
            for url, proto in self.sources:
                f.write(f"#   [{proto}] {url}\n")
            f.write("\n")
        with open(proxy_file, "w", encoding="utf-8") as f:
            for p in proxy_list:
                f.write(p + "\n")
        logger.info(f"Saved {len(proxy_list)} proxies to {proxy_file}")

async def main():
    fetcher = ProxyFetcher()
    logger.info("Fetching proxies ...")
    await fetcher.fetch_all_proxies()
    fetcher.save_proxies()

if __name__ == "__main__":
    asyncio.run(main())
