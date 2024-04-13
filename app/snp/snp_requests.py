from aiohttp import ClientSession, ContentTypeError
from aiohttp_retry import RetryClient, ExponentialRetry
from asyncio.exceptions import CancelledError

from snp.snp_logic import logger
from snp.snp_settings.settings import PARSER


async def get_json_content(session: ClientSession, url: str, params: dict = {}):
    try:
        async with session.get(url, params=params) as resp:
            content = await resp.json()
    except ContentTypeError:
        logger.error(f"Ссылки {url} - нет")
        return
    except CancelledError:
        await session.close()

    return content


async def get_page_content(url: str):
    try:
        retry_options = ExponentialRetry(attempts=PARSER.retry_attempt)
        async with RetryClient(retry_options=retry_options) as session:
            async with session.get(url) as resp:
                content = await resp.text()
    except ContentTypeError:
        logger.error(f"Ссылки {url} - нет")
        return
    except CancelledError:
        await session.close()

    return content
