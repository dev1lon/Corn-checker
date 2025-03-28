import asyncio
import aiohttp
from fake_useragent import UserAgent
from eth_account import Account
from eth_account.messages import encode_defunct

from utils import logger


logger = logger.get_logger()


class Corn:
    def __init__(self, private_key, proxy, semaphore):
        self.private_key = private_key
        self.proxy = f'http://{proxy}'
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.semaphore = semaphore

    async def checker(self):
        for attempt in range(0, 3):
            try:
                async with self.semaphore:
                    headers = {
                        'user-agent': UserAgent().random
                    }
                    async with aiohttp.request(method='GET',url=f'https://api.usecorn.com/api/v1/auth/login/{self.address}',headers=headers, proxy=self.proxy) as response:
                        data = await response.json()
                        message = data['message']
                        encoded_message = encode_defunct(text=message)

                    signed_message = self.account.sign_message(encoded_message)
                    signature = signed_message.signature.hex()
                    json_data = {'siweMessage': message, 'signature': signature}

                    async with aiohttp.request(method='POST',url=f'https://api.usecorn.com/api/v1/auth/login',headers=headers, json=json_data, proxy=self.proxy) as response:
                        data = await response.json()
                        token_login = data['token']
                        json_data = {'token': token_login, 'returnSecureToken': True}

                    async with aiohttp.request(method='POST', url=f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyCkirF_4-bK6zbvYFL0V9bm2Vd5KEkI2eQ',headers=headers, json=json_data, proxy=self.proxy) as response:
                        data = await response.json()
                        token = data['idToken']
                        params = self.address
                        headers_claim = {
                            'authorization': f'Bearer {token}',
                            'user-agent': UserAgent().random
                        }

                    async with aiohttp.request(method='GET',url=f'https://api.usecorn.com/api/v1/claims/claim',params=params, headers=headers_claim, proxy=self.proxy) as response:
                        data = await response.json()
                        if response.status == 404:
                            logger.success(f'{self.address} | Not Eligible')
                            await asyncio.sleep(1)
                            return False
                        allocation = data['allocation']
                        logger.success(f'{self.address} | Allocation - {allocation}')
                        await asyncio.sleep(1)
                        return True

            except Exception as err:
                logger.warning(f'{self.address} | {err} |  Retry')
                await asyncio.sleep(15)
