import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from database import Database

from dotenv import load_dotenv
import os
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    studying_style = State()
    studying_card = State()


load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()
db = Database()

menu_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Помощь")],
        [types.KeyboardButton(text="О проекте")],
        [types.KeyboardButton(text="Профиль")],
        [types.KeyboardButton(text="Продолжить изучение")]
    ],
    resize_keyboard=True
)

study_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Изучение новых идиом")],
        [types.KeyboardButton(text="Повторение изученных идиом")]
    ],
    resize_keyboard=True
)

card_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Следующая идиома")],
        [types.KeyboardButton(text="В меню")]
    ],
    resize_keyboard=True
)

answer_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Показать ответ")]
    ],
    resize_keyboard=True
)

know_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Знаю")],
        [types.KeyboardButton(text="Не знаю")]
    ],
    resize_keyboard=True
)


async def on_startup():
    await db.connect()
    logging.info('Бот и БД готовы к работе')


@dp.message(Command('start'))
async def start(message: types.Message):
    await db.get_or_create_user(message.from_user.id)
    await message.answer(f"Привет! Добро пожаловать в бота для изучения итальянских идиом!", reply_markup=menu_keyboard)


@dp.message(F.text.lower() == "/help")
async def helpeng(message: types.Message):
    await message.reply("Место для текста о помощи!")


@dp.message(F.text.lower() == "помощь")
async def helprus(message: types.Message):
    await message.reply("Место для текста о помощи!")


@dp.message(F.text.lower() == "/about")
async def abouteng(message: types.Message):
    await message.reply("Место для текста о проекте!")


@dp.message(F.text.lower() == "о проекте")
async def aboutrus(message: types.Message):
    await message.reply("Место для текста о проекте!")


@dp.message(F.text.lower() == "профиль")
async def profile(message: types.Message):
    user = await db.get_or_create_user(message.from_user.id)
    learned = await db.get_learned_cards(user['user_id'])
    await message.answer(f"Твой id: {user['user_id']}\nИдиом выучено: {learned}")


@dp.message(F.text.lower() == "продолжить изучение")
async def study_deck(message: types.Message, state: FSMContext):
    await message.answer(f"Как вы хотите продолжить изучение?", reply_markup=study_keyboard)


@dp.message(F.text.lower() == "изучение новых идиом")
async def learning(message: types.Message, state: FSMContext):
    user = await db.get_or_create_user(message.from_user.id)
    card = await db.get_unknown_card(user['user_id'])
    if not card:
        await message.reply("Вы выучили все идиомы! Начините повторение", reply_markup=study_keyboard)
        return

    await state.set_state(UserStates.studying_card)
    await state.update_data(selected_card=card)
    await state.set_state(UserStates.studying_style)
    await state.update_data(studying_style="learning")

    await message.reply(f"Идиома: {card}", reply_markup=answer_keyboard)


@dp.message(F.text.lower() == "повторение изученных идиом")
async def repetition(message: types.Message, state: FSMContext):
    user = await db.get_or_create_user(message.from_user.id)
    card = await db.get_known_card(user['user_id'])
    if not card:
        await message.reply("Вы ещё не выучили ни одной идиомы! Начините изучение", reply_markup=study_keyboard)
        return

    await state.set_state(UserStates.studying_card)
    await state.update_data(selected_card=card)
    await state.set_state(UserStates.studying_style)
    await state.update_data(studying_style="repetition")

    await message.reply(f"Карточка: {card}", reply_markup=answer_keyboard)


@dp.message(F.text.lower() == "показать ответ")
async def answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_card = data.get('selected_card')
    studying_style = data.get('studying_style')
    if not selected_card:
        await message.reply("И какой ответ тут должен быть?", reply_markup=menu_keyboard)
        return

    ans = await db.get_card_answer(selected_card)
    if not ans:
        await message.reply("У этой идиомы нет ответа...", reply_markup=study_keyboard)
        return

    if studying_style == "repetition":
        await message.reply(f"Ответ: {ans}", reply_markup=card_keyboard)
    elif studying_style == "learning":
        await message.reply(f"Ответ: {ans}", reply_markup=know_keyboard)


@dp.message(F.text.lower() == "знаю")
async def know(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_card = data.get('selected_card')
    if not selected_card:
        await message.reply("И что ты знаешь?", reply_markup=menu_keyboard)
        return

    card_id = await db.get_card_id(selected_card)
    user_id = await db.get_or_create_user(message.from_user.id)
    await db.add_known_card(user_id['user_id'], card_id)
    await message.answer(f"Молодец!", reply_markup=card_keyboard)


@dp.message(F.text.lower() == "не знаю")
async def dunno(message: types.Message):
    await message.answer(f"Ну ничего, выучишь :)", reply_markup=card_keyboard)


@dp.message(F.text.lower() == "следующая идиома")
async def next_card(message: types.Message, state: FSMContext):
    data = await state.get_data()
    studying_style = data.get('studying_style')

    if studying_style == "repetition":
        await repetition(message, state)
    elif studying_style == "learning":
        await learning(message, state)
    else:
        await message.reply("Пожалуйста, выберите действие из меню", reply_markup=menu_keyboard)


@dp.message(F.text.lower() == "в меню")
async def menu(message: types.Message):
    await message.reply("Меню:", reply_markup=menu_keyboard)


async def main():
    await on_startup()
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    import asyncio

    asyncio.run(main())
