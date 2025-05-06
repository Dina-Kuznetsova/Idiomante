-- Пользователи (минимальная версия)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL
);

-- Карточки в колодах
CREATE TABLE cards (
    card_id SERIAL PRIMARY KEY,
    front_text TEXT NOT NULL,
    back_text TEXT NOT NULL
);

-- Прогресс изучения карточек
CREATE TABLE user_cards (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    card_id INTEGER REFERENCES cards(card_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, card_id)
);