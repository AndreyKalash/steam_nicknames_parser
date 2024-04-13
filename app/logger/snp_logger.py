import logging

from customtkinter import END, CTkTextbox


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# добавляем новый уровень
SUCCESS = 25
logging.addLevelName(SUCCESS, "SUCCESS")

# задаем формат
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class TextHandler(logging.Handler):
    """Хендлкр позволяющий дублировать логи в QUI"""

    def __init__(self, widget: CTkTextbox):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        """Функция для записи в textbox"""
        # устанавливаем режим редактирования
        self.widget.configure(state="normal")
        tag = record.levelname
        # вставляем текст в конец
        self.widget.insert(
            END, f"{record.asctime} - {record.levelname} - {record.message}\n", tag
        )
        self.widget.see(END)
        # устанавливаем режим только для чтения
        self.widget.configure(state="disabled")


def set_logger_handler(widget: CTkTextbox):
    """Функция для привязки textbox к логгеру"""
    text_handler = TextHandler(widget)
    logger.addHandler(text_handler)
