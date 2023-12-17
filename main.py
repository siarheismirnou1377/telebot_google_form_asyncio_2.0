import random
import logging
import asyncio

import requests
from bs4 import BeautifulSoup

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message,ReplyKeyboardMarkup
# ДОДЕЛАТЬ ЛОГГИРОВАНИЕ!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ---->
# Нужно логировать все ошибки как-то

class FormUrl(StatesGroup):
    # Класс состояния url
    url = State()
    
form_router = Router()
# Ссылка которую можно задать через бота    
url_text = '' 
# Параметр работы цикла проверки
stop_while = False  

# Создаем объект логгера
logger = logging.getLogger('my_logger')
# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# Создание обработчиков логирования
file_handler = logging.FileHandler('my_log.txt') # Для записи логов в файл
# Добавляем файловый обработчик к логгеру
logger.addHandler(file_handler)

async def main():  
    # Запуск бота
    bot = Bot('токен', parse_mode=ParseMode.HTML)  # В кавычки вставить токен
    dp = Dispatcher()
    dp.include_router(form_router)
    await dp.start_polling(bot)


@form_router.message(CommandStart())  
async def start_bot(message: Message):
    # Хендлим команду старт и запускаем бота 
    kb = [[KeyboardButton(text="Начать"), KeyboardButton(text="Задать ссылку"), KeyboardButton(text="Остановить")],]
    keyboard = ReplyKeyboardMarkup(keyboard=kb)
 
    await message.reply(f"Привет, {(message.from_user.full_name)}! Нажми 'Задать ссылку', а потом 'Начать', чтобы отслеживать форму.",
                        reply_markup=keyboard)
    
    # Записываем информацию в лог
    logger.info(f"Пользователь id = {message.from_user.id} name = {(message.from_user.full_name)} вызвал команду /start")

""" @form_router.message(Command("mycommand"))  # Запуск бота по собственной команде
async def start_bot(message: Message):
    # Хендлим команду и запускаем бота 
    kb = [[KeyboardButton(text="Начать"), KeyboardButton(text="Задать ссылку"), KeyboardButton(text="Остановить")],]
    keyboard = ReplyKeyboardMarkup(keyboard=kb)
 
    await message.reply(f"Привет, {(message.from_user.full_name)}! Нажми 'Задать ссылку', а потом 'Начать', чтобы отслеживать форму.",
                        reply_markup=keyboard) """

@form_router.message(F.text == "Начать")  
async def parser_form(message: Message):
    # Парсинг формы и проверка  
    global url_text 
    global stop_while
    stop_while = True
    count = 0
    await message.answer("Начал отслеживать форму. Чтобы остановить процесс проверки и/или задать новую ссылку, сначала нажми 'Остановить.'")    
    # Записываем информацию в лог
    logger.info(f"Пользователь id = {message.from_user.id} name = {(message.from_user.full_name)} вызвал команду 'Начать'.")
    while stop_while:
        interval = random.randint(1, 120)
        response = requests.get(url_text)
        bs = BeautifulSoup(response.text, "lxml")
        soup =  bs.find(class_="UatU5d")
        elem_soup = BeautifulSoup(str(soup), 'html.parser')
        elem_soup = elem_soup.text

        if soup and count == 0:  # Если сродержт тег и это первый запуск
            await message.answer(text=elem_soup)
            count = 1
            await asyncio.sleep(interval)
            continue
        if soup and count == 1:  # Если содержит тег и это >= 2 запуску
            await asyncio.sleep(interval)
            continue
        if not soup and count >= 0:  # Если не содержит тег 
            await message.answer("Ссылка формы изменила свой статус. Проверь ссылку{0}".format(url_text))
            count = 0
            break

@form_router.message(F.text == "Остановить")  
async def parser_form(message: Message):
    global stop_while
    stop_while = False
    await message.answer("Остановил проверку. Чтобы запустить, задай ссылку и нажми 'Начать'.")
    logger.info(f"Пользователь id = {message.from_user.id} name = {(message.from_user.full_name)} вызвал команду 'Остановить'.")   
     
@form_router.message(F.text == "Задать ссылку")
# Отслеживаем "Задать ссылку"
async def start_url(message: Message, state: FSMContext):
    await state.set_state(FormUrl.url)
    await message.answer("Скопируй ссылку и отправь мне. Затем, нажми 'Начать'.")
    logger.info(f"Пользователь id = {message.from_user.id} name = {(message.from_user.full_name)} вызвал команду 'Задать ссылку'.")

@form_router.message(FormUrl.url)
async def process_url(message: Message, state: FSMContext):
    global url_text
    url_text_local = await state.update_data(url=message.text)
    url_text = url_text_local['url']
    # Тут проверка валидности ссылки
    try:
        check = requests.head(url_text)
        if check.status_code == 200:
            await message.answer("Принял ссылку.Нажми 'Начать'.")
        else:
            await message.answer("Ссылка не валидна. Проверь ссылку и нажми 'Задать ссылку' снова.")
    except requests.exceptions.MissingSchema:
        await message.answer("Это не ссылка. Нажми 'Задать ссылку' снова. чтобы ввести правильный адрес.")
        logger.exception(f"Пользователь id = {message.from_user.id} name = {(message.from_user.full_name)} ввёл неправильную ссылку {requests.exceptions.MissingSchema}")


if __name__ == "__main__":
    asyncio.run(main())