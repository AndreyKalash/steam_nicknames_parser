import asyncio
import os
import re
import threading

import customtkinter as ctk
import pandas as pd

from tkinter import filedialog, messagebox

from PIL import Image


from snp.snp_logic import start, stop
from logger.snp_logger import logger, set_logger_handler


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class SNP(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.build_gui()

    def build_gui(self):
        """Метод для отрисовки GUI"""
        # устанавливаем размеры окна
        self.geometry("1200x600+450+180")
        self.minsize(1200, 600)
        self.maxsize(1200, 600)

        self.title("SNP - steam nicknames parser")

        # устанавливаем хендлер на закрытие окна
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # -------------------- Поля ввода -------------------- #
        self.save_folder_label = ctk.CTkLabel(
            master=self,
            text="Введите путь до папки для сохранения xslx файла",
            font=("Courier", 18),
        )
        self.save_folder_label.place(relx=0.04, rely=0.1)

        self.save_dir_path_entry = ctk.CTkEntry(
            master=self,
            placeholder_text="Введите путь",
            width=472,
            height=40,
            border_width=2,
            corner_radius=10,
        )
        self.save_dir_path_entry.place(relx=0.04, rely=0.15)

        self.photoimage = ctk.CTkImage(
            Image.open("app\\static\\folder_icon.png"), size=(25, 25)
        )

        self.choose_folder_btn = ctk.CTkButton(
            master=self,
            image=self.photoimage,
            height=40,
            width=40,
            text="",
            fg_color=self.save_dir_path_entry._fg_color,
            border_color=self.save_dir_path_entry._border_color,
            border_width=2,
            corner_radius=10,
            hover_color=self._fg_color,
            command=self.choose_folder_handler,
        )
        self.choose_folder_btn.place(relx=0.44, rely=0.15)

        self.output_file_name_label = ctk.CTkLabel(
            master=self, text="Введите название отчета xslx", font=("Courier", 18)
        )
        self.output_file_name_label.place(relx=0.04, rely=0.25)

        self.output_file_name_entry = ctk.CTkEntry(
            master=self,
            placeholder_text="output / output.xslx",
            width=472,
            height=40,
            border_width=2,
            corner_radius=10,
            fg_color=self.save_dir_path_entry._fg_color,
            border_color=self.save_dir_path_entry._border_color,
        )
        self.output_file_name_entry.place(relx=0.04, rely=0.3)

        self.nickname_requred = ctk.CTkLabel(
            master=self, text="Введите никнейм для парсинга", font=("Courier", 18)
        )
        self.nickname_requred.place(relx=0.04, rely=0.4)

        self.nickname_requred_entry = ctk.CTkEntry(
            master=self,
            placeholder_text="Введите никнейм",
            width=472,
            height=40,
            border_width=2,
            corner_radius=10,
            fg_color=self.save_dir_path_entry._fg_color,
            border_color=self.save_dir_path_entry._border_color,
        )
        self.nickname_requred_entry.place(relx=0.04, rely=0.45)
        self.nickname_requred_entry.insert(0, "Тут ник")

        # -------------------- Старт -------------------- #
        self.start_button = ctk.CTkButton(
            master=self,
            text="Начать",
            width=250,
            height=70,
            font=("Courier", 24),
            corner_radius=10,
            border_width=2,
            hover_color="#14375e",
            command=self.start_button_handler,
        )
        self.start_button.place(relx=0.13, rely=0.65)

        # -------------------- Логи -------------------- #
        self.log_frame = ctk.CTkTextbox(
            master=self, width=500, height=400, font=("Courier", 12)
        )
        self.log_frame.place(relx=0.53, rely=0.1)
        # устанавливаем режим только для чтения
        self.log_frame.configure(state="disabled")
        # окраска текста для определенных имен уровней логгера
        self.log_frame.tag_config("ERROR", foreground="#f44336")
        self.log_frame.tag_config("INFO", foreground="#2986cc")
        self.log_frame.tag_config("SUCCESS", foreground="#8fce00")
        # привязка логгера к текстбоксу
        set_logger_handler(self.log_frame)

        # -------------------- Прогресс бар -------------------- #
        self.progress_bar = ctk.CTkProgressBar(
            master=self,
            width=1090,
            height=30,
            mode="determinate",
        )
        self.progress_bar.place(relx=0.04, rely=0.87)
        self.progress_bar.set(0)

    def choose_folder_handler(self):
        """Хендлер кнопки для выбора папки"""
        self.save_dir_path = filedialog.askdirectory(initialdir="C:/")
        self.save_dir_path_entry.delete(0, ctk.END)
        self.save_dir_path_entry.insert(0, self.save_dir_path)

    def start_button_handler(self):
        """Хендлер кнопки старт"""
        self.save_dir_path = self.save_dir_path_entry.get().strip()
        self.file_name = self.output_file_name_entry.get().strip()
        self.nickname = self.nickname_requred_entry.get().strip()

        # проверяем данные на валидность
        valid_data = self.validation()
        if valid_data:
            # запускаем поток с парсером
            thread = threading.Thread(target=self.start_parsing_handler)
            thread.start()

    def start_parsing_handler(self):
        # запускаем парсер и создаем отчет
        res = start(self.nickname, self.loop, self.progress_bar)
        if all(res):
            self.create_xslx(*res)

    def on_closing(self):
        """Хендлер закрытия окна. Останавливает текущие задачи"""
        stop(self.loop)
        self.destroy()
        exit()

    def create_xslx(self, rows_list, users_count):
        """Формирование отчета xlsx"""
        logger.info("Формирование отчета...")
        df = pd.DataFrame()
        for rows in rows_list:
            new_df = pd.DataFrame(rows)
            df = pd.concat([df, new_df], ignore_index=True)

        # logger.info("Удаление дубликатов")
        # df.drop_duplicates(inplace=True)
        logger.info(f"Отчет содержит {len(df)} из {users_count} строк")
        df.to_excel(self.full_path, index=False)
        logger.info(f"Отчет {self.full_path} - создан")
        messagebox.showinfo("Отчет создан", "Отчет создан")

    def validation(self):
        """Функция для проверки даннх на валидность"""
        valid_data = False
        if not self.save_dir_path:
            logger.error("Не введено название папки")
            messagebox.showerror("ERROR", "Введите название папки")
        elif not os.path.exists(self.save_dir_path):
            logger.error("Введеная папка не существует")
            messagebox.showerror("ERROR", "Введеная папка не существует")
        elif not self.file_name:
            logger.error("Не введено название файла")
            messagebox.showerror("ERROR", "Введите название файла")
        elif re.search(r'[/:*?"<>|\\\\]+', self.file_name):
            logger.error("Имя файла содержит запрещеные знаки")
            messagebox.showerror(
                "ERROR", 'Имя файла не должно содержать следующих знаков:\n\/:*?"<>|'
            )
        elif not self.nickname:
            logger.error("Не введен никнейм")
            messagebox.showerror("ERROR", "Никнейм не может быть пустой")
        elif self.save_dir_path and self.file_name:
            if not self.file_name.endswith(".xlsx"):
                self.file_name += ".xlsx"
            self.full_path = os.path.join(self.save_dir_path, self.file_name)
            if os.path.exists(self.full_path):
                logger.error(f"Файл {self.full_path} уже существует!")
                messagebox.showerror("ERROR", f"Файл {self.full_path} уже существует!")
            else:
                valid_data = True
        else:
            valid_data = True

        return valid_data
