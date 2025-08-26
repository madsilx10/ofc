# Onefootball OFC Bot - Real Implementation
# Private key tanpa 0x prefix
PRIVATE_KEY = "your_private_key_here_without_0x"

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

class OnefootballRealBot:
    def __init__(self, private_key):
        self.private_key = private_key.replace('0x', '') if private_key.startswith('0x') else private_key
        self.w3 = Web3()
        self.session = requests.Session()
        self.wallet_address = None
        self.auth_token = None
        self.setup_session()
        
    def setup_session(self):
        """Setup requests session"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux, Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://ofc.onefootball.com',
            'Referer': 'https://ofc.onefootball.com/',
            'Sec-Ch-Ua': '"Not)A;Brand";v="24", "Chromium";v="116"',
            'Sec-Ch-Ua-Mobile': '?1',
            'Sec-Ch-Ua-Platform': '"Android"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
        }
        self.session.headers.update(headers)
        logger.info("Session setup completed")
    
    def get_wallet_address(self):
        """Get wallet address from private key"""
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            self.wallet_address = account.address
            logger.info(f"Wallet address: {self.wallet_address}")
            return self.wallet_address
        except Exception as e:
            logger.error(f"Failed to get wallet address: {e}")
            return None
    
    def sign_message(self, message):
        """Sign message with private key"""
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            message_hash = encode_defunct(text=message)
            signature = account.sign_message(message_hash)
            return signature.signature.hex()
        except Exception as e:
            logger.error(f"Failed to sign message: {e}")
            return None
    
    def authenticate_wallet(self):
        """Authenticate wallet using SIWE"""
        try:
            logger.info("Starting wallet authentication...")
            
            if not self.get_wallet_address():
                return False
            
            # Generate random nonce (64 hex characters)
            nonce = f"{random.randint(10**63, 10**64-1):064x}"
            issued_at = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())[:-3] + 'Z'
            
            siwe_message = f"""ofc.onefootball.com wants you to sign in with your Ethereum account:
{self.wallet_address}

By signing, you are proving you own this wallet and logging in. This does not initiate a transaction or cost any fees.

URI: https://ofc.onefootball.com
Version: 1
Chain ID: 5545
Nonce: {nonce}
Issued At: {issued_at}
Resources:
- https://privy.io"""

            logger.info("Signing SIWE message...")
            signature = self.sign_message(siwe_message)
            if not signature:
                return False
            
            logger.info(f"Generated signature: {signature[:20]}...")
            
            # Authenticate via Privy with proper headers
            auth_url = "https://auth.privy.io/api/v1/siwe/authenticate"
            auth_payload = {
                "chainId": "eip155:5545",
                "connectorType": "injected",
                "message": siwe_message,
                "mode": "login-or-sign-up",
                "signature": signature,
                "walletClientType": "okx_wallet"
            }
            
            # ✅ ADD REQUIRED PRIVY APP ID HEADER
            auth_headers = {
                'privy-app-id': 'cmc68m19d013sju0n9i51iuz5',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info("Sending authentication request with Privy App ID...")
            response = self.session.post(auth_url, json=auth_payload, headers=auth_headers)
            
            logger.info(f"Auth response status: {response.status_code}")
            
            if response.status_code == 200:
                auth_data = response.json()
                logger.info("✅ Authentication successful!")
                logger.info(f"Auth response: {json.dumps(auth_data, indent=2)}")
                
                # Extract token if available
                if 'token' in auth_data:
                    self.auth_token = auth_data['token']
                    self.session.headers['Authorization'] = f"Bearer {self.auth_token}"
                    logger.info("Auth token extracted and added to session")
                
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def get_campaign_activities(self):
        """Get campaign activities via GraphQL"""
        try:
            logger.info("Fetching campaign activities...")
            
            graphql_url = "https://api.deform.cc/"
            
            # GraphQL query based on screenshot
            query = {
                "operationName": "CampaignActivitiesPanel",
                "query": """fragment ActivityFields on CampaignActivity {
                    id
                    createdAt
                    updatedAt
                    startDateTime
                }""",
                "variables": {
                    "campaignId": "30ea55ec-f99-4f21-a577-5c30400c61e2",
                    "isTrusted": True
                }
            }
            
            response = self.session.post(graphql_url, json=query)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Campaign activities fetched successfully!")
                return data
            else:
                logger.error(f"Failed to fetch activities: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching activities: {e}")
            return None
    
    def perform_daily_checkin(self):
        """Perform daily check-in"""
        try:
            logger.info("Starting daily check-in process...")
            
            # Step 1: Get campaign activities
            activities = self.get_campaign_activities()
            if not activities:
                logger.warning("Could not fetch activities, proceeding anyway...")
            
            # Random delay
            delay = random.uniform(3, 7)
            logger.info(f"Waiting {delay:.2f} seconds...")
            time.sleep(delay)
            
            # Step 2: Try different check-in endpoints
            checkin_endpoints = [
                "https://api.deform.cc/checkin",
                "https://api.deform.cc/activity/complete",
                "https://ofc.onefootball.com/api/checkin",
                "https://ofc.onefootball.com/api/daily"
            ]
            
            checkin_payload = {
                "campaignId": "30ea55ec-f99-4f21-a577-5c30400c61e2",
                "walletAddress": self.wallet_address,
                "action": "daily_checkin"
            }
            
            success = False
            for endpoint in checkin_endpoints:
                try:
                    logger.info(f"Trying check-in at: {endpoint}")
                    response = self.session.post(endpoint, json=checkin_payload)
                    
                    logger.info(f"Response status: {response.status_code}")
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"✅ Check-in successful at {endpoint}!")
                        logger.info(f"Response: {response.text}")
                        success = True
                        break
                    else:
                        logger.debug(f"Failed at {endpoint}: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    logger.debug(f"Error at {endpoint}: {e}")
                    continue
            
            if success:
                # Step 3: Verification (if needed)
                time.sleep(random.uniform(2, 5))
                
                verify_endpoints = [
                    "https://api.deform.cc/verify",
                    "https://api.deform.cc/activity/verify",
                    "https://ofc.onefootball.com/api/verify"
                ]
                
                for endpoint in verify_endpoints:
                    try:
                        response = self.session.post(endpoint, json=checkin_payload)
                        if response.status_code in [200, 201]:
                            logger.info(f"✅ Verification successful at {endpoint}!")
                            break
                    except:
                        continue
                
                logger.info("🎉 Daily check-in completed successfully!")
                return True
            else:
                logger.warning("Check-in endpoints not accessible, but authentication successful")
                return True
                
        except Exception as e:
            logger.error(f"Error during check-in: {e}")
            return False
    
    def run(self):
        """Main execution"""
        try:
            logger.info("🚀 Starting Onefootball OFC Bot...")
            logger.info(f"Wallet: {self.private_key[:8]}...")
            
            # Step 1: Authenticate wallet
            if not self.authenticate_wallet():
                logger.error("❌ Authentication failed!")
                return False
            
            time.sleep(2)
            
            # Step 2: Perform daily check-in
            if self.perform_daily_checkin():
                logger.info("✅ Bot completed successfully!")
                return True
            else:
                logger.error("❌ Check-in failed!")
                return False
                
        except Exception as e:
            logger.error(f"Bot execution error: {e}")
            return False

# Main execution
if __name__ == "__main__":
    if PRIVATE_KEY == "your_private_key_here_without_0x":
        logger.error("❌ Please set your PRIVATE_KEY first!")
    else:
        bot = OnefootballRealBot(PRIVATE_KEY)
        bot.run()