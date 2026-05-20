import asyncio
import random
import os
import asyncpg

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN") or "8567616083:AAHFlvVNPm9hClfUOQpDBB4RxRN1MdiwfzA"
ADMIN_ID = 8465432674

EVENT_MULTIPLIER = 1

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================

db = None

async def db_start():
    global db

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL не найден в Variables Railway")

    db = await asyncpg.connect(
        database_url,
        ssl="require"
    )

    # USERS
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            money BIGINT DEFAULT 0,
            power BIGINT DEFAULT 1,
            autoclick BIGINT DEFAULT 0,
            vip BIGINT DEFAULT 0
        )
    """)

    # PROMOCODES
    await db.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            reward BIGINT,
            activations BIGINT
        )
    """)

    # PROMO USES
    await db.execute("""
        CREATE TABLE IF NOT EXISTS promo_uses (
            user_id BIGINT,
            code TEXT,
            PRIMARY KEY (user_id, code)
        )
    """)


async def create_user(user_id):
    await db.execute("""
        INSERT INTO users (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO NOTHING
    """, user_id)


async def get_user(user_id):
    await create_user(user_id)

    row = await db.fetchrow("""
        SELECT money, power, autoclick, vip
        FROM users
        WHERE user_id = $1
    """, user_id)

    if row:
        return (
            row["money"],
            row["power"],
            row["autoclick"],
            row["vip"]
        )

    return (0, 1, 0, 0)

# ================= VIP =================

def vip_multiplier(vip):

    if vip == 1:
        return 2

    elif vip == 2:
        return 5

    elif vip == 3:
        return 10

    return 1

# ================= MENU =================

def menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💰 Клик",
                    callback_data="click"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🛒 Улучшить",
                    callback_data="upgrade"
                ),

                InlineKeyboardButton(
                    text="🤖 Автоклик",
                    callback_data="autoclick"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎰 Казино",
                    callback_data="casino"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎁 Промокод",
                    callback_data="promo_menu"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 Профиль",
                    callback_data="profile"
                ),

                InlineKeyboardButton(
                    text="🏆 Топ",
                    callback_data="top"
                )
            ]
        ]
    )

# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):

    await create_user(message.from_user.id)

    await message.answer(
        "🎮 CLICKER BOT\n\nДобро пожаловать!",
        reply_markup=menu()
    )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    money, power, autoclick, vip = user

    await callback.message.edit_text(
        f"👤 ПРОФИЛЬ\n\n"
        f"💰 Монеты: {money}\n"
        f"⚡ Сила: {power}\n"
        f"🤖 Автоклик: {autoclick}\n"
        f"💎 VIP: {vip}",
        reply_markup=menu()
    )

# ================= CLICK =================

@dp.callback_query(F.data == "click")
async def click(callback: CallbackQuery):
    global EVENT_MULTIPLIER

    user_id = callback.from_user.id
    money, power, autoclick, vip = await get_user(user_id)

    vip_bonus = vip_multiplier(vip)
    earn = power * vip_bonus * EVENT_MULTIPLIER

    await db.execute("""
        UPDATE users
        SET money = money + $1
        WHERE user_id = $2
    """, earn, user_id)

    money, power, autoclick, vip = await get_user(user_id)

    await callback.message.edit_text(
        f"💰 +{earn} монет\n\n"
        f"💵 Баланс: {money}\n"
        f"⚡ Сила: {power}\n"
        f"💎 VIP x{vip_bonus}\n"
        f"🎉 EVENT x{EVENT_MULTIPLIER}",
        reply_markup=menu()
    )

    await callback.answer()


# ================= UPGRADE =================

@dp.callback_query(F.data == "upgrade")
async def upgrade(callback: CallbackQuery):
    user_id = callback.from_user.id
    money, power, autoclick, vip = await get_user(user_id)

    price = power * 50

    if money >= price:
        await db.execute("""
            UPDATE users
            SET money = money - $1,
                power = power + 1
            WHERE user_id = $2
        """, price, user_id)

        money, power, autoclick, vip = await get_user(user_id)

        text = (
            f"🚀 Улучшение куплено!\n\n"
            f"⚡ Сила: {power}\n"
            f"💰 Баланс: {money}"
        )
    else:
        text = f"❌ Нужно {price} монет"

    await callback.message.edit_text(
        text,
        reply_markup=menu()
    )

    await callback.answer()


# ================= AUTOCLICK =================

@dp.callback_query(F.data == "autoclick")
async def autoclick(callback: CallbackQuery):
    user_id = callback.from_user.id
    money, power, autoclick_level, vip = await get_user(user_id)

    price = (autoclick_level + 1) * 200

    if money >= price:
        await db.execute("""
            UPDATE users
            SET money = money - $1,
                autoclick = autoclick + 1
            WHERE user_id = $2
        """, price, user_id)

        money, power, autoclick_level, vip = await get_user(user_id)

        text = (
            f"🤖 Автоклик улучшен!\n\n"
            f"🤖 Уровень: {autoclick_level}\n"
            f"💰 Баланс: {money}"
        )
    else:
        text = f"❌ Нужно {price} монет"

    await callback.message.edit_text(
        text,
        reply_markup=menu()
    )

    await callback.answer()


# ================= TOP =================

@dp.callback_query(F.data == "top")
async def top(callback: CallbackQuery):
    rows = await db.fetch("""
        SELECT user_id, money
        FROM users
        ORDER BY money DESC
        LIMIT 10
    """)

    text = "🏆 ТОП ИГРОКОВ\n\n"

    for i, row in enumerate(rows, start=1):
        text += f"{i}. ID {row['user_id']} — {row['money']} 💰\n"

    await callback.message.edit_text(
        text,
        reply_markup=menu()
    )

    await callback.answer()

# ================= CASINO =================

@dp.message(Command("casino"))
async def casino(message: Message):
    args = message.text.split()

    if len(args) != 2:
        await message.answer(
            "🎰 Использование:\n"
            "/casino ставка"
        )
        return

    user_id = message.from_user.id

    try:
        bet = int(args[1])
    except:
        await message.answer(
            "❌ Ставка должна быть числом"
        )
        return

    if bet <= 0:
        await message.answer(
            "❌ Ставка должна быть больше 0"
        )
        return

    # Получаем данные пользователя (и создаем его при необходимости)
    money, power, autoclick, vip = await get_user(user_id)

    if money < bet:
        await message.answer(
            "❌ Недостаточно монет"
        )
        return

    # Шанс выигрыша 20%
    if random.randint(1, 100) <= 20:
        win = bet * 2
        money += win

        text = (
            f"🎰 ВЫ ВЫИГРАЛИ!\n\n"
            f"💰 Ставка: {bet}\n"
            f"🔥 Выигрыш: {win}\n"
            f"💵 Баланс: {money}"
        )
    else:
        money -= bet

        text = (
            f"💀 ВЫ ПРОИГРАЛИ\n\n"
            f"💸 Потеряно: {bet}\n"
            f"💵 Баланс: {money}"
        )

    # Сохраняем новый баланс
    await db.execute("""
        UPDATE users
        SET money = $1
        WHERE user_id = $2
    """, money, user_id)

    await message.answer(text)

# ================= CASINO BUTTON =================

@dp.callback_query(F.data == "casino")
async def casino_button(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎰 КАЗИНО\n\n"
        "Использование:\n"
        "/casino ставка\n\n"
        "Пример:\n"
        "/casino 1000",
        reply_markup=menu()
    )

# ================= PROMO MENU =================

@dp.callback_query(F.data == "promo_menu")
async def promo_menu(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎁 Чтобы активировать промокод:\n\n"
        "Напишите:\n"
        "/promo код",
        reply_markup=menu()
    )

@dp.message(Command("addpromo"))
async def addpromo(message: Message):
    # Только администратор
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 4:
        await message.answer(
            "Использование:\n"
            "/addpromo КОД награда активации\n\n"
            "Пример:\n"
            "/addpromo START 1000 10"
        )
        return

    code = args[1].upper()

    try:
        reward = int(args[2])
        activations = int(args[3])
    except:
        await message.answer("❌ Награда и активации должны быть числами")
        return

    if reward <= 0 or activations <= 0:
        await message.answer("❌ Числа должны быть больше 0")
        return

    # Создаем или обновляем промокод
    await db.execute("""
        INSERT INTO promocodes (code, reward, activations)
        VALUES ($1, $2, $3)
        ON CONFLICT (code)
        DO UPDATE SET
            reward = EXCLUDED.reward,
            activations = EXCLUDED.activations
    """, code, reward, activations)

    await message.answer(
        f"✅ Промокод создан!\n\n"
        f"🎁 Код: {code}\n"
        f"💰 Награда: {reward}\n"
        f"🔢 Активаций: {activations}"
    )

# ================= EVENT =================

@dp.message(Command("event"))
async def event(message: Message):

    global EVENT_MULTIPLIER

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 3:

        await message.answer(
            "/event multiplier seconds"
        )

        return

    multiplier = int(args[1])
    seconds = int(args[2])

    EVENT_MULTIPLIER = multiplier

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            "SELECT user_id FROM users"
        )

        users = await cursor.fetchall()

    for user in users:

        try:

            await bot.send_message(
                user[0],
                f"🎉 ГЛОБАЛЬНЫЙ ИВЕНТ!\n\n"
                f"🔥 Доход x{multiplier}\n"
                f"⏳ Время: {seconds} секунд"
            )

        except:
            pass

    await asyncio.sleep(seconds)

    EVENT_MULTIPLIER = 1

    for user in users:

        try:

            await bot.send_message(
                user[0],
                "❌ Ивент закончился"
            )

        except:
            pass
           
# ================= STOP EVENT =================

@dp.message(Command("stopevent"))
async def stopevent(message: Message):

    global EVENT_MULTIPLIER

    if message.from_user.id != ADMIN_ID:
        return

    EVENT_MULTIPLIER = 1

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            "SELECT user_id FROM users"
        )

        users = await cursor.fetchall()

    for user in users:

        try:

            await bot.send_message(
                user[0],
                "❌ Администратор остановил ивент"
            )

        except:
            pass

    await message.answer(
        "✅ Ивент остановлен"
    )
    
# ================= GIVE VIP =================

@dp.message(Command("givevip"))
async def givevip(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 3:

        await message.answer(
            "/givevip user_id vip"
        )

        return

    user_id = int(args[1])
    vip = int(args[2])

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        UPDATE users
        SET vip = ?
        WHERE user_id = ?
        """, (vip, user_id))

        await db.commit()

    await bot.send_message(
        user_id,
        f"💎 Вам выдан VIP {vip}"
    )

    await message.answer(
        "✅ VIP выдан"
    )

# ================= REMOVE VIP =================

@dp.message(Command("removevip"))
async def removevip(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 2:

        await message.answer(
            "/removevip user_id"
        )

        return

    user_id = int(args[1])

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        UPDATE users
        SET vip = 0
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()

    await bot.send_message(
        user_id,
        "❌ Ваш VIP был забран"
    )

    await message.answer(
        "✅ VIP забран"
    )

# ================= BROADCAST =================

@dp.message(Command("broadcast"))
async def broadcast(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace(
        "/broadcast ",
        ""
    )

    if text == "/broadcast" or text.strip() == "":

        await message.answer(
            "❌ Использование:\n"
            "/broadcast текст"
        )

        return

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            "SELECT user_id FROM users"
        )

        users = await cursor.fetchall()

    sent = 0

    for user in users:

        try:

            await bot.send_message(
                user[0],
                f"📢 ОБЪЯВЛЕНИЕ\n\n{text}"
            )

            sent += 1

        except:
            pass

    await message.answer(
        f"✅ Рассылка отправлена\n"
        f"👥 Получили: {sent}"
    )
    
# ================= GIVE MONEY =================

@dp.message(Command("givemoney"))
async def givemoney(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 3:

        await message.answer(
            "/givemoney user_id amount"
        )

        return

    user_id = int(args[1])
    amount = int(args[2])

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        UPDATE users
        SET money = money + ?
        WHERE user_id = ?
        """, (amount, user_id))

        await db.commit()

    await bot.send_message(
        user_id,
        f"💰 Вам выдано {amount} монет!"
    )

    await message.answer(
        "✅ Деньги выданы"
    )

# ================= REMOVE MONEY =================

@dp.message(Command("removemoney"))
async def removemoney(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 3:

        await message.answer(
            "/removemoney user_id amount"
        )

        return

    user_id = int(args[1])
    amount = int(args[2])

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT money
        FROM users
        WHERE user_id = ?
        """, (user_id,))

        user = await cursor.fetchone()

        if user is None:

            await message.answer(
                "❌ Игрок не найден"
            )

            return

        money = user[0] - amount

        if money < 0:
            money = 0

        await db.execute("""
        UPDATE users
        SET money = ?
        WHERE user_id = ?
        """, (money, user_id))

        await db.commit()

    await bot.send_message(
        user_id,
        f"💸 У вас забрали {amount} монет"
    )

    await message.answer(
        "✅ Деньги забраны"
    )
    
# ================= AUTO FARM =================

async def auto_farm():

    while True:

        async with aiosqlite.connect(DB_PATH) as db:

            cursor = await db.execute("""
            SELECT user_id, autoclick
            FROM users
            """)

            users = await cursor.fetchall()

            for user in users:

                user_id = user[0]
                autoclick = user[1]

                if autoclick > 0:

                    await db.execute("""
                    UPDATE users
                    SET money = money + ?
                    WHERE user_id = ?
                    """, (autoclick, user_id))

            await db.commit()

        await asyncio.sleep(5)

# ================= MAIN =================

async def main():

    await db_start()

    asyncio.create_task(auto_farm())

    print("Бот запущен")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
