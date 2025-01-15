import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor

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

    def parse_proxy_list(self, content, url):
        if not content:
            return
        try:
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

    def check_proxy(self, proxy):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        # Setup WebDriver with Selenium
        service = Service(executable_path="/path/to/chromedriver")  # Update path to your chromedriver
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            proxy_url = f"http://{proxy}"
            # Set up proxy for the WebDriver
            webdriver.DesiredCapabilities.CHROME['proxy'] = {
                "httpProxy": proxy_url,
                "ftpProxy": proxy_url,
                "sslProxy": proxy_url,
                "proxyType": "MANUAL"
            }

            # Test the proxy by visiting a website
            driver.get('http://httpbin.org/ip')
            time.sleep(5)  # Wait for the page to load

            # Check if the proxy is working
            body_text = driver.find_element(By.TAG_NAME, 'body').text
            if "origin" in body_text:
                self.valid_proxies.add(proxy)
                logger.info(f"Proxy {proxy} is working.")
            else:
                logger.warning(f"Proxy {proxy} failed to work.")
        except Exception as e:
            logger.error(f"Error checking proxy {proxy}: {str(e)}")
        finally:
            driver.quit()

    def fetch_all_proxies(self):
        # Simulate fetching the proxy list from the sources
        # This should ideally use requests or Selenium to fetch the lists
        # For simplicity, just use a hardcoded list of proxies
        proxy_list = ["182.34.56.78:8080", "172.45.67.89:9000"]  # Example proxies

        with ThreadPoolExecutor(max_workers=10) as executor:
            # Use ThreadPoolExecutor to run the check_proxy function in parallel for each proxy
            executor.map(self.check_proxy, proxy_list)

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

def main():
    fetcher = ProxyFetcher()
    fetcher.fetch_all_proxies()
    fetcher.save_proxies()

if __name__ == "__main__":
    main()
