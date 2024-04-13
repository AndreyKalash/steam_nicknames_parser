from dataclasses import dataclass

from snp.snp_settings.config_reader import parser_config, snp_config


@dataclass
class PARSER:
    """
    настройки парсинга

    fields:
        retry_attempt: int - количество повторений, если сервер отклонил запрос
        sliced_by: int количество асинхронного парсинга страниц в асинхронной задаче
    """

    retry_attempt = int(parser_config["parser"]["retry_attempt"])
    sliced_by = int(parser_config["parser"]["sliced_by"])


@dataclass
class COOKIE:
    """
    необходимые куки для парсинга

    fields:
        session_id: str - название куки хранящее id сессии
    """

    session_id: str = parser_config["cookies"]["session_id"]


@dataclass
class URL:
    """
    ссылки для получения информации пользователей

    fields:
        search_base_url: str - базовая ссылка для получения пользователей на странице поиска
        nicknames_base_url: str - базовая ссылка для получения никнеймов пользователя. в плейсхолдер передается id/profiles пользователя

    """

    search_base_url: str = parser_config["urls"]["search_base_url"]
    nicknames_base_url: str = parser_config["urls"]["nicknames_base_url"]

    class FIELD:
        """
        необходимые куки для парсинга

        fields:
            html: str - поле для URL.search_base_url хранящее html с карточками пользователей
            result_count: str - поле для URL.search_base_urlхранящее количества найденых ников
            nickname: str - поле для URL.nicknames_base_url хранящее ник в истории ников
        """

        html: str = parser_config["json_fields"]["html"]
        result_count: str = parser_config["json_fields"]["result_count"]
        nickname: str = parser_config["json_fields"]["nickname"]


@dataclass
class SELECTOR:
    """
    селекторы для парсинга html

    fields:
        user_boxes: str - карточка пользователя на странице поиска
        user_a_tag: str - ссылка на профиль пользователя в карточке пользователя
        user_description: str - описание в профиле пользователя
    """

    user_boxes: str = parser_config["selectors"]["user_boxes"]
    user_a_tag: str = parser_config["selectors"]["user_a_tag"]
    user_description: str = parser_config["selectors"]["user_description"]


@dataclass
class EXCEL_FIELD:
    """
    названия хедров столбцов в excel отчете с данными пользоватей

    fields:
        url: str - столбец с ссылкой на профиль пользователя
        description: str - столбец с описанием пользователя
        location: str - столбец с страной, городом пользователя
        name: str - столбец с именем пользователя
        nickname: str - столбцы с никнеймами. в плейсхолдере хранятся числа от 1 до 10
    """

    url: str = snp_config["excel_fields"]["url"]
    description: str = snp_config["excel_fields"]["description"]
    location: str = snp_config["excel_fields"]["location"]
    name: str = snp_config["excel_fields"]["name"]
    nickname: str = snp_config["excel_fields"]["nickname"]
