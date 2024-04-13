import asyncio
import re

from aiohttp import ClientSession
from bs4 import BeautifulSoup, Tag

from logger.snp_logger import logger, SUCCESS
from snp.snp_requests import get_page_content, get_json_content
from snp.snp_settings.settings import EXCEL_FIELD, SELECTOR, URL


async def get_page_users_info(
    html,
    return_pages_count: bool,
    session: ClientSession,
    loop: asyncio.AbstractEventLoop,
):
    """
    Функция для парсинга информации пользователей с одной страницы поиска

    Args:
        html: html структура, содержащая карточки профилей
        return_pages_count (bool): при значении True вернет количество пользователей на странице. False - список с информацей пользователей
        session (ClientSession): асинхронная сессия
        loop (AbstractEventLoop): текущий event_loop для асинхронного парсинга

    Returns:
        return_pages_count == True
            количество пользователей на странице

        return_pages_count == Flase
            rows (List[List[Dict]]): список с данными аккаунтов на стриницe
    """
    soup = BeautifulSoup(html, "html.parser")
    user_boxes = soup.select(SELECTOR.user_boxes)

    if return_pages_count:
        return len(user_boxes)

    user_parse_tasks = [
        loop.create_task(get_user_info(user_box, session)) for user_box in user_boxes
    ]
    rows = await asyncio.gather(*user_parse_tasks)

    return rows


async def get_user_info(user: Tag, session: ClientSession) -> dict:
    """
    Функция для парсинга информации пользователя

    Args:
        user (Tag): карточка пользователя
        session (ClientSession): асинхронная сессия

    Returns:
        return_pages_count == True
            количество пользователей на странице

        return_pages_count == Flase
            row (dict): словарь с данными аккаунта
    """
    # ищем ссылку в карточке пользователя
    user_a_tag = user.select_one(SELECTOR.user_a_tag)
    # получаем ссылку на профиль
    profile_url = user_a_tag.get("href")
    # получаем текст в карточке пользователя
    user_text = user.text
    # ищем иконку страны
    img = user.find("img")
    # получаем id|profiles пользователя
    user_id_path = profile_url.rsplit("https://steamcommunity.com/", 1)[1]

    location_and_name = get_user_preview_info(user_text, bool(img))
    user_description = await get_user_description(profile_url)
    user_nicknames = await get_user_nicknames(session, user_id_path)
    if not user_nicknames:
        user_nicknames = {EXCEL_FIELD.nickname.format(1): user_a_tag.text.strip()}

    # объединяем полученные значения
    row = {
        EXCEL_FIELD.url: profile_url,
        EXCEL_FIELD.description: user_description,
        **location_and_name,
        **user_nicknames,
    }

    logger.log(SUCCESS, f"Получены данные по аккаунту - {profile_url}")
    return row


def get_user_preview_info(text: str, img_icon: Tag = None) -> dict:
    """
    Функция для получения локации и имени указаных в профиле

    Args:
        text (str): текст в карточке пользователя
        img_icon (Union[Tag, None]): иконка страны. None если ее нет

    Returns:
        res (dict): с локацией и именем пользователя
    """
    res = {EXCEL_FIELD.location: None, EXCEL_FIELD.name: None}
    # убираем лишние символы
    for_empt = ["\n", "\xa0"]
    text = text.strip()
    for symb in for_empt:
        text = text.replace(symb, "")
    # разбиваем текст по табуляции
    text_parts = re.split(r"\t+", text)

    # если только ник - возвращаем словарь с пустыми значениями имени и локации
    if len(text_parts) == 1:
        return res
    # если 2 элемента и один из них иконка страны - добавляем локацию
    elif len(text_parts) == 2 and img_icon:
        res[EXCEL_FIELD.location] = text_parts[1]
    # если 2 элемента и нет иконки - добавляем имя
    elif len(text_parts) == 2 and not img_icon:
        res[EXCEL_FIELD.name] = text_parts[1]
    # добавляем имя и локацию
    else:
        res.update(
            {EXCEL_FIELD.location: text_parts[2], EXCEL_FIELD.name: text_parts[1]}
        )

    return res


async def get_user_description(user_url: str) -> str:
    """
    Функция для получения описания указаных в профиле

    Args:
        user_url (str): ссылка на профиль пользователя

    Returns:
        user_description (str): описание в профиле
    """
    content = await get_page_content(user_url)
    if not content:
        return
    soup = BeautifulSoup(content, "html.parser")

    user_description = soup.select_one(SELECTOR.user_description)
    if not user_description:
        return
    user_description = user_description.text.strip()

    return user_description


async def get_user_nicknames(
    session: ClientSession, user_id_path: str
) -> dict | None:
    """
    Функция для получения никнеймов пользователя

    Args:
        session (ClientSession): асинхронная сессия
        user_id_path (str): id|profiles пользователя

    Returns:
        nicknames (Union[Dict, None]): словарь с никнеймами пользователя. None если их нет
    """
    nicknames_base_url = URL.nicknames_base_url
    nicknames_url = nicknames_base_url.format(user_id_path)

    content = await get_json_content(session, nicknames_url)
    if not content:
        return

    nicknames = {}
    for i, nickname_dict in enumerate(content, 1):
        nickname = nickname_dict[URL.FIELD.nickname]
        nicknames[EXCEL_FIELD.nickname.format(i)] = nickname

    return nicknames
