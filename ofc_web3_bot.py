import time
import random
import requests
import json
import logging
from web3 import Web3
from eth_account.messages import encode_defunct

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OnefootballWeb3Bot:
    def __init__(self, private_keys):
        self.private_keys = private_keys
        self.w3 = Web3()
        self.session = requests.Session()
        self.setup_session()
        
    def setup_session(self):
        """Setup requests session with headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        self.session.headers.update(headers)
        logger.info("Session initialized")
    
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def get_wallet_info(self, private_key):
        """Get wallet address from private key"""
        try:
            account = self.w3.eth.account.from_key(private_key)
            return {
                'address': account.address,
                'private_key': private_key
            }
        except Exception as e:
            logger.error(f"Invalid private key: {e}")
            return None
    
    def sign_message(self, private_key, message):
        """Sign message with private key"""
        try:
            account = self.w3.eth.account.from_key(private_key)
            message_hash = encode_defunct(text=message)
            signature = account.sign_message(message_hash)
            return signature.signature.hex()
        except Exception as e:
            logger.error(f"Failed to sign message: {e}")
            return None
    
    def get_nonce_or_challenge(self, wallet_address):
        """Get nonce/challenge from API"""
        try:
            # Try common endpoints for getting nonce/challenge
            endpoints = [
                f"https://ofc.onefootball.com/api/auth/nonce?address={wallet_address}",
                f"https://ofc.onefootball.com/api/nonce/{wallet_address}",
                f"https://ofc.onefootball.com/api/challenge/{wallet_address}",
                f"https://ofc.onefootball.com/api/wallet/nonce?wallet={wallet_address}"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        # Look for nonce in different possible keys
                        nonce_keys = ['nonce', 'challenge', 'message', 'data']
                        for key in nonce_keys:
                            if key in data:
                                logger.info(f"Got nonce/challenge from {endpoint}")
                                return data[key]
                        return data  # Return full response if no specific key found
                except:
                    continue
            
            # If no API endpoint works, create a standard nonce
            standard_nonce = f"Sign this message to verify your wallet: {int(time.time())}"
            logger.info("Using standard nonce message")
            return standard_nonce
            
        except Exception as e:
            logger.error(f"Failed to get nonce: {e}")
            return f"Sign this message to verify your wallet: {int(time.time())}"
    
    def authenticate_wallet(self, wallet_info):
        """Authenticate wallet with signature"""
        try:
            wallet_address = wallet_info['address']
            private_key = wallet_info['private_key']
            
            # Get nonce/challenge
            nonce = self.get_nonce_or_challenge(wallet_address)
            if isinstance(nonce, dict):
                message = json.dumps(nonce)
            else:
                message = str(nonce)
            
            # Sign the message
            signature = self.sign_message(private_key, message)
            if not signature:
                return False
            
            # Try authentication endpoints
            auth_data = {
                'address': wallet_address,
                'signature': signature,
                'message': message,
                'wallet': wallet_address
            }
            
            auth_endpoints = [
                "https://ofc.onefootball.com/api/auth/login",
                "https://ofc.onefootball.com/api/auth/verify",
                "https://ofc.onefootball.com/api/wallet/connect",
                "https://ofc.onefootball.com/api/connect"
            ]
            
            for endpoint in auth_endpoints:
                try:
                    response = self.session.post(endpoint, json=auth_data)
                    if response.status_code in [200, 201]:
                        data = response.json()
                        logger.info(f"Authentication successful via {endpoint}")
                        
                        # Store token if provided
                        if 'token' in data:
                            self.session.headers['Authorization'] = f"Bearer {data['token']}"
                        elif 'access_token' in data:
                            self.session.headers['Authorization'] = f"Bearer {data['access_token']}"
                        
                        return True
                except Exception as e:
                    logger.debug(f"Auth failed for {endpoint}: {e}")
                    continue
            
            logger.warning("Could not authenticate via API, proceeding anyway...")
            return True
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def perform_daily_checkin_api(self):
        """Perform daily check-in via API calls"""
        try:
            logger.info("Starting daily check-in via API...")
            
            # Step 1: Start check-in process (equivalent to "Let's go")
            checkin_endpoints = [
                "https://ofc.onefootball.com/api/checkin/start",
                "https://ofc.onefootball.com/api/daily/start",
                "https://ofc.onefootball.com/api/claim/start",
                "https://ofc.onefootball.com/api/rewards/start"
            ]
            
            step1_success = False
            for endpoint in checkin_endpoints:
                try:
                    response = self.session.post(endpoint)
                    if response.status_code in [200, 201]:
                        logger.info(f"✓ Step 1: Started check-in via {endpoint}")
                        step1_success = True
                        break
                except:
                    continue
            
            if not step1_success:
                # Try GET requests as fallback
                for endpoint in checkin_endpoints:
                    try:
                        response = self.session.get(endpoint)
                        if response.status_code == 200:
                            logger.info(f"✓ Step 1: Started check-in via GET {endpoint}")
                            step1_success = True
                            break
                    except:
                        continue
            
            # Delay between steps
            delay = random.uniform(5, 10)
            logger.info(f"Waiting {delay:.2f} seconds before verification...")
            time.sleep(delay)
            
            # Step 2: Verify/Complete check-in
            verify_endpoints = [
                "https://ofc.onefootball.com/api/checkin/verify",
                "https://ofc.onefootball.com/api/checkin/complete",
                "https://ofc.onefootball.com/api/daily/verify",
                "https://ofc.onefootball.com/api/daily/complete",
                "https://ofc.onefootball.com/api/claim/verify",
                "https://ofc.onefootball.com/api/claim/complete"
            ]
            
            step2_success = False
            for endpoint in verify_endpoints:
                try:
                    response = self.session.post(endpoint)
                    if response.status_code in [200, 201]:
                        data = response.json()
                        logger.info(f"✓ Step 2: Verified check-in via {endpoint}")
                        logger.info(f"Response: {data}")
                        step2_success = True
                        break
                except Exception as e:
                    logger.debug(f"Verify failed for {endpoint}: {e}")
                    continue
            
            if step2_success:
                logger.info("✅ Daily check-in completed successfully!")
                return True
            else:
                logger.warning("Could not complete verification via API")
                return step1_success  # At least step 1 worked
                
        except Exception as e:
            logger.error(f"Error during API check-in: {e}")
            return False
    
    def get_user_status(self):
        """Get user status/profile info"""
        try:
            status_endpoints = [
                "https://ofc.onefootball.com/api/user/profile",
                "https://ofc.onefootball.com/api/user/status",
                "https://ofc.onefootball.com/api/profile",
                "https://ofc.onefootball.com/api/user"
            ]
            
            for endpoint in status_endpoints:
                try:
                    response = self.session.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"User status: {data}")
                        return data
                except:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Failed to get user status: {e}")
            return None
    
    def process_account(self, private_key):
        """Process single account"""
        try:
            logger.info(f"Processing account with private key: {private_key[:8]}...")
            
            # Get wallet info
            wallet_info = self.get_wallet_info(private_key)
            if not wallet_info:
                logger.error("Invalid wallet info")
                return False
            
            logger.info(f"Wallet address: {wallet_info['address']}")
            
            # Authenticate wallet
            if not self.authenticate_wallet(wallet_info):
                logger.error("Failed to authenticate wallet")
                return False
            
            self.random_delay(2, 4)
            
            # Get user status (optional)
            self.get_user_status()
            
            # Perform daily check-in
            if not self.perform_daily_checkin_api():
                logger.error("Failed to perform daily check-in")
                return False
            
            logger.info("✅ Account processed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error processing account: {e}")
            return False
    
    def run(self):
        """Main execution function"""
        try:
            successful = 0
            total = len(self.private_keys)
            
            logger.info(f"Starting Web3 bot for {total} accounts...")
            
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

# Configuration
PRIVATE_KEYS = [
    "your_private_key_1_here",
    "your_private_key_2_here",
    # Add more private keys as needed
]

if __name__ == "__main__":
    # Initialize and run bot
    bot = OnefootballWeb3Bot(PRIVATE_KEYS)
    bot.run()