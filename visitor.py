import yaml
import time
import random
import subprocess
import logging
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from fake_useragent import UserAgent

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VisitorOrchestrator:
    def __init__(self, config_path='config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.ua = UserAgent()

    def rotate_vpn(self):
        """Connects to a new NordVPN location based on weighted probability."""
        locations = self.config['locations']
        weights = [loc['weight'] for loc in locations]
        selected = random.choices(locations, weights=weights, k=1)[0]
        
        logger.info(f"Rotating VPN to: {selected['country']} ({selected['nord_name']})")
        
        try:
            # Disconnect first to be clean
            subprocess.run(['nordvpn', 'disconnect'], capture_output=True)
            # Connect to new location
            result = subprocess.run(['nordvpn', 'connect', selected['nord_name']], 
                                 capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to connect to VPN: {result.stderr}")
                return False
            return True
        except Exception as e:
            logger.error(f"VPN rotation error: {e}")
            return False

    def get_random_persona(self):
        """Generates a random hardware/software fingerprint."""
        return {
            'user_agent': self.ua.random,
            'viewport': {
                'width': random.randint(1280, 1920),
                'height': random.randint(720, 1080)
            },
            'device_scale_factor': random.choice([1, 1.25, 1.5, 2]),
            'is_mobile': False,
            'has_touch': False,
        }

    def perform_visit(self, url):
        """Executes a stealthy browser visit."""
        persona = self.get_random_persona()
        browser_config = self.config['browsers']
        browser_type = random.choices(
            [b['type'] for b in browser_config], 
            weights=[b['weight'] for b in browser_config], 
            k=1
        )[0]

        with sync_playwright() as p:
            browser_engine = getattr(p, browser_type)
            browser = browser_engine.launch(headless=True)
            
            # Create a fresh context (no cookies, no cache)
            context = browser.new_context(
                user_agent=persona['user_agent'],
                viewport=persona['viewport'],
                device_scale_factor=persona['device_scale_factor']
            )
            
            page = context.new_page()
            
            # Apply stealth plugins
            stealth_sync(page)
            
            logger.info(f"Visiting {url} using {browser_type} as {persona['user_agent'][:50]}...")
            
            try:
                # Randomize wait time before navigation to simulate human typing/clicking
                time.sleep(random.uniform(2, 5))
                
                page.goto(url, wait_until='networkidle')
                
                # Simulate human behavior: scroll down
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                time.sleep(random.uniform(5, 15))
                
                logger.info(f"Visit successful: {page.title()}")
            except Exception as e:
                logger.error(f"Visit failed: {e}")
            finally:
                browser.close()

    def run(self, url):
        """Main loop for 24/7 operation."""
        while True:
            if self.rotate_vpn():
                self.perform_visit(url)
            
                # Randomized delay before next visit
                delay = random.randint(
                    self.config['jitter']['min_delay'], 
                    self.config['jitter']['max_delay']
                )
                logger.info(f"Sleeping for {delay}s until next visit...")
                time.sleep(delay)
            else:
                logger.warning("Retrying VPN rotation in 60s...")
                time.sleep(60)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python visitor.py <url>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    orchestrator = VisitorOrchestrator()
    orchestrator.run(target_url)
