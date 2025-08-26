import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
from web3 import Web3

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OnefootballBot:
    def __init__(self, private_keys, headless=True):
        self.private_keys = private_keys
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome driver with necessary options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        try:
            # Auto-install ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("Chrome driver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            return False
    
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def connect_wallet(self, private_key):
        """Connect wallet using private key"""
        try:
            # Create Web3 account from private key
            w3 = Web3()
            account = w3.eth.account.from_key(private_key)
            wallet_address = account.address
            logger.info(f"Wallet address: {wallet_address}")
            
            # Look for connect wallet button
            connect_selectors = [
                "button[class*='connect']",
                "button[class*='wallet']",
                "button:contains('Connect')",
                "button:contains('Wallet')",
                "[class*='connect-wallet']"
            ]
            
            wallet_connected = False
            for selector in connect_selectors:
                try:
                    if 'contains' in selector:
                        # Use XPath for text-based search
                        xpath = f"//button[contains(text(), '{selector.split(':contains(')[1][2:-3]}')]"
                        connect_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    else:
                        connect_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    connect_btn.click()
                    logger.info(f"Clicked connect wallet button with selector: {selector}")
                    wallet_connected = True
                    break
                except:
                    continue
            
            if not wallet_connected:
                logger.warning("Could not find connect wallet button, trying alternative methods")
                # Try clicking any button that might be for wallet connection
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    btn_text = btn.text.lower()
                    if any(word in btn_text for word in ['connect', 'wallet', 'login', 'sign']):
                        btn.click()
                        logger.info(f"Clicked button with text: {btn.text}")
                        break
            
            self.random_delay(3, 6)
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect wallet: {e}")
            return False
    
    def perform_daily_checkin(self):
        """Perform daily check-in process"""
        try:
            logger.info("Starting daily check-in process...")
            
            # Step 1: Look for "Let's go" button
            lets_go_selectors = [
                "button:contains('Let\\'s go')",
                "button:contains('Lets go')",
                "button[class*='lets-go']",
                "button[class*='start']",
                "[class*='lets-go']"
            ]
            
            step1_completed = False
            for selector in lets_go_selectors:
                try:
                    if 'contains' in selector:
                        text = selector.split(':contains(')[1][2:-3]
                        xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
                        lets_go_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    else:
                        lets_go_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    lets_go_btn.click()
                    logger.info(f"✓ Step 1: Clicked 'Let's go' button")
                    step1_completed = True
                    break
                except:
                    continue
            
            if not step1_completed:
                # Fallback: find any button with relevant text
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    btn_text = btn.text.lower()
                    if any(word in btn_text for word in ['go', 'start', 'begin', 'continue']):
                        btn.click()
                        logger.info(f"✓ Step 1: Clicked button with text: {btn.text}")
                        step1_completed = True
                        break
            
            if not step1_completed:
                logger.error("Could not find 'Let's go' button")
                return False
            
            # Wait delay between steps
            delay = random.uniform(5, 10)
            logger.info(f"Waiting {delay:.2f} seconds before verification...")
            time.sleep(delay)
            
            # Step 2: Look for "Verify" button
            verify_selectors = [
                "button:contains('Verify')",
                "button:contains('Confirm')",
                "button[class*='verify']",
                "button[class*='confirm']",
                "[class*='verify']"
            ]
            
            step2_completed = False
            for selector in verify_selectors:
                try:
                    if 'contains' in selector:
                        text = selector.split(':contains(')[1][2:-3]
                        xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
                        verify_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    else:
                        verify_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    verify_btn.click()
                    logger.info(f"✓ Step 2: Clicked 'Verify' button")
                    step2_completed = True
                    break
                except:
                    continue
            
            if not step2_completed:
                # Fallback: find any button with relevant text
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    btn_text = btn.text.lower()
                    if any(word in btn_text for word in ['verify', 'confirm', 'submit', 'complete']):
                        btn.click()
                        logger.info(f"✓ Step 2: Clicked button with text: {btn.text}")
                        step2_completed = True
                        break
            
            if step2_completed:
                logger.info("✅ Daily check-in completed successfully!")
                self.random_delay(3, 6)
                return True
            else:
                logger.error("Could not complete verification step")
                return False
                
        except Exception as e:
            logger.error(f"Error during daily check-in: {e}")
            return False
    
    def process_account(self, private_key):
        """Process single account"""
        try:
            logger.info(f"Processing account with private key: {private_key[:8]}...")
            
            # Navigate to website
            self.driver.get("https://ofc.onefootball.com/s2")
            self.random_delay(5, 8)
            
            # Connect wallet
            if not self.connect_wallet(private_key):
                logger.error("Failed to connect wallet")
                return False
            
            # Perform daily check-in
            if not self.perform_daily_checkin():
                logger.error("Failed to perform daily check-in")
                return False
            
            logger.info("✅ Account processed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error processing account: {e}")
            return False
    
    def run(self):
        """Main execution function"""
        if not self.setup_driver():
            logger.error("Failed to setup driver")
            return
        
        try:
            successful = 0
            total = len(self.private_keys)
            
            logger.info(f"Starting bot for {total} accounts...")
            
            for i, private_key in enumerate(self.private_keys, 1):
                logger.info(f"Processing account {i}/{total}")
                
                if self.process_account(private_key):
                    successful += 1
                
                # Delay between accounts
                if i < total:
                    delay = random.uniform(10, 20)
                    logger.info(f"Waiting {delay:.2f} seconds before next account...")
                    time.sleep(delay)
            
            logger.info(f"✅ Bot completed! {successful}/{total} accounts processed successfully")
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")

# Configuration
PRIVATE_KEYS = [
    "your_private_key_1_here",
    "your_private_key_2_here",
    # Add more private keys as needed
]

if __name__ == "__main__":
    # Initialize and run bot
    bot = OnefootballBot(PRIVATE_KEYS, headless=False)  # Set headless=True for background mode
    bot.run()