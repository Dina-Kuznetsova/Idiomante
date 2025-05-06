import asyncpg
from dotenv import load_dotenv
import os
import logging

load_dotenv()


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                min_size=1,
                max_size=10
            )
            logging.info('Успешное подключение к PostgreSQL')
        except Exception as e:
            logging.error(f'Ошибка подключения к БД: {e}')
            raise

    async def get_or_create_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                'INSERT INTO users (telegram_id) VALUES ($1) '
                'ON CONFLICT (telegram_id) DO UPDATE SET telegram_id = $1 RETURNING *',
                user_id
            )
            return user

    async def get_learned_cards(self, user_id: int) -> int:
        async with self.pool.acquire() as conn:
            learned = await conn.fetchrow(
                'SELECT COUNT(*) FROM user_cards WHERE user_id = $1',
                user_id
            )
            return learned['count']

    async def get_unknown_card(self, user_id):
        async with self.pool.acquire() as conn:
            card = await conn.fetchrow(
                'SELECT front_text FROM cards '
                'WHERE card_id NOT IN (SELECT card_id FROM user_cards WHERE user_id = $1) '
                'ORDER BY RANDOM()',
                user_id
            )
            return card['front_text'] if card else None

    async def get_known_card(self, user_id):
        async with self.pool.acquire() as conn:
            card = await conn.fetchrow(
                'SELECT front_text FROM cards '
                'WHERE card_id IN (SELECT card_id FROM user_cards WHERE user_id = $1) '
                'ORDER BY RANDOM()',
                user_id
            )
            return card['front_text'] if card else None

    async def get_card_answer(self, card_front):
        async with self.pool.acquire() as conn:
            card_answer = await conn.fetchrow(
                'SELECT back_text FROM cards WHERE front_text = $1',
                card_front
            )
            return card_answer['back_text'] if card_answer else None

    async def get_card_id(self, card_front):
        async with self.pool.acquire() as conn:
            card_id = await conn.fetchrow(
                'SELECT card_id FROM cards WHERE front_text = $1',
                card_front
            )
            return card_id['card_id']

    async def add_known_card(self, user_id, card_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO user_cards (user_id, card_id) VALUES ($1, $2)',
                user_id,
                card_id
            )
