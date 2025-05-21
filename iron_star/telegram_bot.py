import requests
import telebot
import time
from threading import Thread
from dataclasses import dataclass, field
from iron_star.polling import is_registration_open
import json
from pathlib import Path
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = '8194226321:AAGyWFDAc0qobuOXt01CFM5lF0kxsLkIci4'
URL = 'https://iron-star.com/event/ironstar-1-8-sirius-sochi-2025/'


@dataclass
class State:
    context_file: Path = Path(__file__).parent / 'context.json'
    subscribed_chats: set = field(default_factory=set)
    is_ready: bool = False

    def save_context(self):
        with open(self.context_file, 'w') as f:
            try:
                data = {
                    'subscribed_chats': list(self.subscribed_chats),
                    'is_ready': self.is_ready,
                }
                json.dump(data, f)
            except Exception as ex:
                print('Ошибка при сериализации контекста')
                raise ex

    def load_context(self):
        if not self.context_file.is_file():
            print('Файл контекста не обнаружен')
            return
        with open(self.context_file, 'r', encoding='utf-8') as f:
            try:
                context = json.load(f)
                self.subscribed_chats = set(context['subscribed_chats'])
                self.is_ready = context['is_ready']
            except Exception as ex:
                print('Кривой файл контекста')


@dataclass
class TelegramBot:
    bot: telebot.TeleBot = telebot.TeleBot(TOKEN)
    state: State = State()

    _errors: str = field(init=False, default_factory=str)

    def __post_init__(self):
        self.menu_keyboard = self.create_menu_keyboard()
        self.register_handlers()
        self.state.load_context()
        self.working = True
        self._th = Thread(target=self.check_registration_state)
        self._th.daemon = True
        self._th.start()
        print('Bot is running...')
        self.bot.infinity_polling()

    def create_menu_keyboard(self):
        """Create a custom reply keyboard with menu commands"""
        menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        menu.add(
            KeyboardButton('/start'),
            KeyboardButton('/check'),
        )
        return menu

    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def welcome_handler(message):
            self.send_welcome(message)

        @self.bot.message_handler(commands=['check'])
        def check_value_handler(message):
            self.check_value(message)

        @self.bot.message_handler(commands=['errors'])
        def error_handler(message):
            self.send_errors(message)

        @self.bot.message_handler(commands=['gofman'])
        def error_handler(message):
            self.kill_bot(message)

        @self.bot.message_handler(commands=['ids'])
        def error_handler(message):
            self.get_chat_ids(message)

    def send_welcome(self, message):
        self.state.subscribed_chats.add(message.chat.id)
        msg = (
            'Я вас приветствую! Надеюсь ты в драйве! \n'
            'Я пришлю тебе сообщение, как только '
            'откроется регистрация на iron star 1/8 в октябре. '
            'Это будет полный оверсайз!'
        )
        if self.state.is_ready:
            msg = f'Беги покупать слот! \n {URL}'
        self.bot.send_message(message.chat.id, msg, reply_markup=self.menu_keyboard)

    def check_value(self, message):
        self.state.subscribed_chats.add(message.chat.id)
        self.bot.send_message(
            message.chat.id,
            f'Беги покупать слот! \n {URL}'
            if self.state.is_ready
            else 'Регистрация все еще закрыта',
            reply_markup=self.menu_keyboard,
        )

    def send_errors(self, message):
        self.state.subscribed_chats.add(message.chat.id)
        self.bot.reply_to(
            message,
            self._errors if self._errors else 'Ошибок пока нет',
        )

    def get_chat_ids(self, message):
        self.bot.reply_to(
            message,
            f'{self.state.subscribed_chats}',
        )

    def kill_bot(self, message):
        self.working = False
        self.bot.reply_to(
            message,
            'БОТ ОСТАНОВЛЕН, ВСЕГО ДОБРОГО',
        )
        self.bot.stop_bot()

    def send_message(self):
        for chat_id in self.state.subscribed_chats:
            try:
                self.bot.send_message(
                    chat_id,
                    f'ЁКАРНЫЙ БАБАЙ! ЖМИ! ... на ссылку и покупай слот \n '
                    f'{URL}',
                )
            except Exception as e:
                error_msg = f'Failed to send message to {chat_id}: {e}'
                self._errors += error_msg + '\n'
                print(error_msg)

    def check_registration_state(self):
        while self.working:
            is_ready = False
            try:
                is_ready = is_registration_open(
                    URL, 'Регистрация скоро откроется',
                )
            except requests.RequestException as e:
                error_msg = f'Server connection error {e}'
                self._errors += error_msg + '\n'
                print(error_msg)
            except Exception as e:
                error_msg = f'Server connection error {e}'
                self._errors += error_msg + '\n'
                print(error_msg)
            if not self.state.is_ready and is_ready:
                self.send_message()
                self.state.is_ready = is_ready
            self.state.save_context()
            time.sleep(60)


def main():
    TelegramBot()


if __name__ == '__main__':
    main()
