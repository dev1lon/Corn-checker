import asyncio
from pathlib import Path
import os

from utils import utils, corn, logger


logger = logger.get_logger()


BASE_DIR = Path(__file__).resolve().parent
private_keys = utils.read_file(os.path.join(BASE_DIR, "private_keys.txt"))
proxies = utils.read_file(os.path.join(BASE_DIR, "proxies.txt"))



async def main():
    if len(private_keys) != len(proxies):
        raise Exception('Адреса не соответствуют количеству прокси')
    elif len(private_keys) == 0 or len(proxies) == 0:
        raise Exception('Нет прокси и адресов')

    semaphore = asyncio.Semaphore(5)

    tasks = []
    for private_key, proxy in zip(private_keys, proxies):
        example = corn.Corn(private_key=private_key, proxy=proxy, semaphore=semaphore)
        tasks.append(example.checker())

    results = await asyncio.gather(*tasks)

    eligible_count = sum(1 for result in results if result)
    logger.success(f'Eligible wallets - {eligible_count}')

if __name__ == '__main__':
  asyncio.run(main())