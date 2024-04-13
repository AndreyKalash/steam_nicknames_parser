import asyncio
import time

from asyncio import AbstractEventLoop
from itertools import islice

from aiohttp import ClientConnectionError, ClientSession
from aiohttp_retry import ExponentialRetry, RetryClient
from customtkinter import CTkProgressBar

from logger.snp_logger import logger
from snp.snp_parser import get_page_users_info
from snp.snp_requests import get_json_content
from snp.snp_settings.settings import COOKIE, PARSER, URL


def stop(loop: AbstractEventLoop) -> None:
    """Функция для остановки текущих задач"""
    tasks = asyncio.all_tasks(loop=loop)
    if tasks:
        for task in tasks:
            task.cancel()
        logger.info("Остановка парсера...")

    return


def start(
    nickname: str, loop: AbstractEventLoop, progressbar: CTkProgressBar
) -> tuple:
    """
    Функция для запуска парсера

    Args:
        nickname (str): никнейм для парсинга
        loop (AbstractEventLoop): текущий event_loop для асинхронного парсинга
        progressbar (CTkProgressBar ): экземпляр прогресс бара

    Returns:
        rows (List[List[Dict]]): список с данными аккаунтов на стриницу
        nicks_count (int): количество аккаунтов с заданным ником
    """
    logger.info("Запускаем парсер")
    s = time.time()
    try:
        rows, nicks_count = loop.run_until_complete(
            start_parsing(nickname, progressbar, loop)
        )
    except ClientConnectionError:
        logger.error("Нет подключения к интернету или сервер недоступен")
        stop(loop)
        return [None] * 2

    e = time.time()
    logger.info(f"Время работы - {e-s:.2f} секунд.")
    return rows, nicks_count


async def start_parsing(
    nickname: str, progressbar: CTkProgressBar, loop: AbstractEventLoop
) -> tuple:
    """
    Главная функция асинхронного парсера

    Args:
        nickname (str): Никнейм д парсинга
        progressbar (CTkProgressBar): Прогрессбар для обновлен значений
        loop (AbstractEventLoop): текущий event_loop для асинхронного парсинга (

        Returns:
            rows (List[List[Dict]]): список с данными аккаунтов на стриницу
            nicks_count (int): количество аккаунтов с заданным ником
    """
    # базовая ссылка на json для поиска по никам
    search_base_url = URL.search_base_url
    full_rows = []
    # async with aiohttp.ClientSession() as session:
    retry_options = ExponentialRetry(attempts=PARSER.retry_attempt)
    async with RetryClient(retry_options=retry_options) as session:
        # получаем cookie session_id для успешного парсинга
        session_id = await get_session_id(search_base_url, session)
        logger.info("Ищем страницы")
        # получаем количество страниц поиска в одной асинхронной задаче
        slice_by = PARSER.sliced_by
        # получаем количество страниц поиска, количество одновременного парсинга страниц поиска, количество аккаунтов с ником
        pages, slices, nicks_count = await get_pages_count(
            search_base_url, nickname, session, session_id, loop, slice_by
        )
        # создаем генератор асинхронных задач
        pages_gen = page_tasks_generator(
            search_base_url, nickname, session, session_id, loop, pages
        )
        for _ in range(slices):
            # получаем нужную порцию задач и асинхронно выполняем
            pages_tasks = list(islice(pages_gen, slice_by))
            # получаем аккаунты с страниц и добавляем их в full_rows
            rows_part = await asyncio.gather(*pages_tasks)
            full_rows.extend(rows_part)
            # обновляем прогресс
            progress = len(full_rows) / pages
            progressbar.set(progress)

    return full_rows, nicks_count


async def get_session_id(base_url: str, session: ClientSession) -> str:
    """
    Функция для получения cookie sessionid

    Args:
        base_url (str): корневой путь для поиска по никам
        session (ClientSession): асинхронная сессия

    Returns:
        session_id (str): cookie sessionid
    """
    async with session.get(base_url) as sid_resp:
        session_id = sid_resp.cookies.get(COOKIE.session_id).value

    return session_id


async def get_pages_count(
    search_base_url: str,
    nickname: str,
    session: ClientSession,
    session_id: str,
    loop: AbstractEventLoop,
    slice_by: int,
):
    """
    Функция для получения количества страниц поиска

    Args:
        search_base_url (str): корневой путь для поиска по никам
        nickname (str): никнейм для парсинга
        session (ClientSession): асинхронная сессия
        session_id (str): cookie sessionid
        loop (AbstractEventLoop): текущий event_loop для асинхронного парсинга
        slice_by (int): количество страниц поиска в одной асинхронной задаче

    Returns:
        pages (int): количество страниц поиска
        slices (int): нужное количество задач с страницами поиска
        nicks_count (int): количество найденых профилей с переданным ником

    """
    # получаем количество страниц и количество профилей
    pages, nicks_count = await get_users_info(
        search_base_url, nickname, session, session_id, loop, return_pages_count=True
    )

    logger.info(f"Найдено {pages} страниц")
    # высчитываем нужное количество итераций для сбора страниц поиска
    slices = pages / slice_by
    slices = int(slices) if slices.is_integer() else int(slices) + 1

    return pages, slices, nicks_count


def page_tasks_generator(
    search_base_url: str,
    nickname: str,
    session: ClientSession,
    session_id: str,
    loop: AbstractEventLoop,
    pages: int,
):
    """
    Генератор асинхронных задач для парсинга страницы с поиском

    Args:
        search_base_url (str): корневой путь для поиска по никам
        nickname (str): никнейм для парсинга
        session (ClientSession): асинхронная сессия
        session_id (str): cookie sessionid
        loop (AbstractEventLoop): текущий event_loop для асинхронного парсинга
        pages (int): количество страниц поиска

    Yeilds:
        Task: асинхронная задача на парсинг страницы поиска
    """
    for page in range(1, pages + 1):
        yield asyncio.create_task(
            get_users_info(search_base_url, nickname, session, session_id, loop, page),
            name=f"page_{page}",
        )


async def get_users_info(
    search_base_url: str,
    nickname: str,
    session: ClientSession,
    session_id: str,
    loop: AbstractEventLoop,
    page: int = 1,
    return_pages_count: bool = False,
):
    """
    Функция для получения данных о профилях с одной страницы поиска

    Args:
        search_base_url (str): корневой путь для поиска по никам
        nickname (str): никнейм для парсинга
        session (ClientSession): асинхронная сессия
        session_id (str): cookie sessionid
        loop (AbstractEventLoop): текущий event_loop для асинхронного парсинга
        page (int, optional): номер страницы поиска. по умолчанию 1
        return_pages_count (bool, optional): при значении True возвращает количество ников и страниц. По умолчнаию False

    Returns:
        return_pages_count == True
            pages (int): количество страниц поиска
            nicks_count (int): количество страниц с никнеймом `nickname`

        return_pages_count == False
            users_on_page (list(dict)): список с словарями содержащими информацию о пользователях
    """
    params = {
        "text": nickname,
        "filter": "users",
        "sessionid": session_id,
        "page": page,
    }

    content = await get_json_content(session, search_base_url, params)

    html = content.get("html")
    users_on_page = await get_page_users_info(html, return_pages_count, session, loop)

    # получение количества страниц
    if return_pages_count:
        nicks_count: int = content.get(URL.FIELD.result_count)
        # делим количество всех профилей на количество профилей на одной странице
        pages = nicks_count / users_on_page
        # добавляем 1 если pages не целое (на последней странице меньше страниц чем `users_on_page`)
        pages = int(pages) if pages.is_integer() else int(pages) + 1

        return pages, nicks_count

    logger.info(f"Страница {page} спаршена")
    return users_on_page
