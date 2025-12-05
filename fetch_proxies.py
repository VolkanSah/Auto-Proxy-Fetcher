import aiohttp
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyFetcher:
    def __init__(self):
        self.proxies = set()

        self.sources = [
              ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/http.txt", "http"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/youtube/socks5.txt", "socks5"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/http.txt", "http"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/ClearProxy/checked-proxy-list/main/custom/instagram/socks5.txt", "socks5"),

           ("https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all.txt", "http"),

          ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/http.txt", "http"),
            ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/socks5.txt", "socks5"),
 ("https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt", "http"),
            ("https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt", "socks4"),
            ("https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt", "socks5"),
("https://raw.githubusercontent.com/hookzof/socks5_list/main/proxy.txt", "socks5"),
("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "http"),
        ]

     
    async def fetch_url(self, session, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ProxyFetcher/1.0)',
            }
            timeout = aiohttp.ClientTimeout(total=15)
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return await response.text()
                else:
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

            # Support formats: ip:port, ip:port:user:pass, user:pass@ip:port, http://ip:port
            try:
                # Normalize: strip protocol prefix if present (e.g., "http://1.2.3.4:8080")
                if "://" in line:
                    _, line = line.split("://", 1)
                if "@" in line:
                    auth, hostport = line.split("@", 1)
                    # We ignore auth for now (security risk), but keep host:port
                    line = hostport

                parts = line.split(":")
                if len(parts) < 2:
                    continue

                host = parts[0].strip()
                port = parts[1].split("/")[0].split("#")[0].strip()  # handle trailing comments

                if not port.isdigit():
                    continue
                port_int = int(port)
                if not (1 <= port_int <= 65535):
                    continue

                # Validate IPv4/IPv6 or hostname (basic)
                if "." not in host and ":" not in host:
                    continue  # skip if no dot (likely malformed)

                proxy_url = f"{protocol}://{host}:{port}"
                self.proxies.add(proxy_url)

            except Exception as e:
                continue  # silent skip — malformed line

    async def fetch_all_proxies(self):
        connector = aiohttp.TCPConnector(limit=30, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [self.fetch_url(session, url) for url, _ in self.sources]
            results = await asyncio.gather(*tasks, return_exceptions=False)

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
        os.makedirs("output", exist_ok=True)

        # Save metadata
        with open("output/info.txt", "w", encoding="utf-8") as f:
            f.write(f"# High-Quality Proxy List (Quality-First Aggregation)\n")
            f.write(f"# Updated: {timestamp}\n")
            f.write(f"# Total unique proxies: {len(self.proxies)}\n")
            f.write(f"# Sources: {len(self.sources)} quality-curated URLs\n")
            f.write(f"# Focus: Freshness > Volume | Auto-updated | Verified where possible\n")
            f.write(f"\n# Sources used:\n")
            for url, protocol in self.sources:
                f.write(f"#   [{protocol.upper()}] {url}\n")

        # Save proxies
        with open("output/proxies.txt", "w", encoding="utf-8") as f:
            for proxy in sorted(self.proxies):
                f.write(proxy + "\n")

        logger.info(f"✅ Saved {len(self.proxies)} high-quality proxies to output/proxies.txt")


async def main():
    fetcher = ProxyFetcher()
    logger.info("Starting high-quality proxy fetch...")
    await fetcher.fetch_all_proxies()
    fetcher.save_proxies()


if __name__ == "__main__":
    asyncio.run(main())
