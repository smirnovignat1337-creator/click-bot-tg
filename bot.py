import asyncio
import random
import aiosqlite
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

# ================= CONFIG =================

TOKEN = "8567616083:AAHFlvVNPm9hClfUOQpDBB4RxRN1MdiwfzA"
ADMIN_ID = 8465432674

DB_PATH = "game.db"

EVENT_MULTIPLIER = 1

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================

db = None

async def db_start():
    global db
    db = await asyncpg.connect(os.getenv("DATABASE_URL"))

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
            code TEXT
        )
    """)


async def create_user(user_id):
    await db.execute("""
        INSERT INTO users (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO NOTHING
    """, user_id)


async def get_user(user_id):
    user = await db.fetchrow("""
        SELECT money, power, autoclick, vip
        FROM users
        WHERE user_id = $1
    """, user_id)

    if user:
        return (
            user["money"],
            user["power"],
            user["autoclick"],
            user["vip"]
        )

    return None

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
                ),
                
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
                ),
                InlineKeyboardButton(
                    text="💸 Перевести", 
                    callback_data="pay"
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

# ================= CLICK =================

@dp.callback_query(F.data == "click")
async def click(callback: CallbackQuery):

    global EVENT_MULTIPLIER

    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:

        user = await get_user(user_id)

        money, power, autoclick, vip = user

        vip_bonus = vip_multiplier(vip)

        earn = power * vip_bonus * EVENT_MULTIPLIER

        money += earn

        await db.execute("""
        UPDATE users
        SET money = ?
        WHERE user_id = ?
        """, (money, user_id))

        await db.commit()

    await callback.message.edit_text(
        f"💰 +{earn} монет\n\n"
        f"💵 Баланс: {money}\n"
        f"⚡ Сила: {power}\n"
        f"💎 VIP x{vip_bonus}\n"
        f"🎉 EVENT x{EVENT_MULTIPLIER}",
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

# ================= UPGRADE =================

@dp.callback_query(F.data == "upgrade")
async def upgrade(callback: CallbackQuery):

    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:

        user = await get_user(user_id)

        money, power, autoclick, vip = user

        price = power * 50

        if money >= price:

            money -= price
            power += 1

            await db.execute("""
            UPDATE users
            SET money = ?, power = ?
            WHERE user_id = ?
            """, (money, power, user_id))

            await db.commit()

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

# ================= AUTOCLICK =================

@dp.callback_query(F.data == "autoclick")
async def autoclick(callback: CallbackQuery):

    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:

        user = await get_user(user_id)

        money, power, autoclick, vip = user

        price = (autoclick + 1) * 200

        if money >= price:

            money -= price
            autoclick += 1

            await db.execute("""
            UPDATE users
            SET money = ?, autoclick = ?
            WHERE user_id = ?
            """, (money, autoclick, user_id))

            await db.commit()

            text = (
                f"🤖 Автоклик улучшен!\n\n"
                f"🤖 Уровень: {autoclick}"
            )

        else:
            text = f"❌ Нужно {price} монет"

    await callback.message.edit_text(
        text,
        reply_markup=menu()
    )

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

    async with aiosqlite.connect(DB_PATH) as db:

        user = await get_user(user_id)

        money, power, autoclick, vip = user

        if money < bet:

            await message.answer(
                "❌ Недостаточно монет"
            )

            return

        # ШАНС ВЫИГРЫША

        if random.randint(1, 100) <= 20:

            win = bet * 2

            money += win

            text = (
                f"🎰 ВЫ ВЫИГРАЛИ!\n\n"
                f"💰 Ставка: {bet}\n"
                f"🔥 Выигрыш: {win}"
            )

        else:

            money -= bet

            text = (
                f"💀 ВЫ ПРОИГРАЛИ\n\n"
                f"💸 Потеряно: {bet}"
            )

        await db.execute("""
        UPDATE users
        SET money = ?
        WHERE user_id = ?
        """, (money, user_id))

        await db.commit()

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

# ================= CREATE PROMO =================

@dp.message(Command("createpromo"))
async def createpromo(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) != 4:

        await message.answer(
            "/createpromo code reward activations"
        )

        return

    code = args[1].lower()
    reward = int(args[2])
    activations = int(args[3])

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        INSERT OR REPLACE INTO promocodes
        (code, reward, activations)
        VALUES (?, ?, ?)
        """, (code, reward, activations))

        await db.commit()

    await message.answer(
        f"✅ Промокод {code} создан"
    )

# ================= PROMO =================

@dp.message(Command("promo"))
async def promo(message: Message):

    args = message.text.split()

    if len(args) != 2:

        await message.answer("/promo code")
        return

    user_id = message.from_user.id
    code = args[1].lower()

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT reward, activations
        FROM promocodes
        WHERE code = ?
        """, (code,))

        promo = await cursor.fetchone()

        if promo is None:

            await message.answer(
                "❌ Промокод не найден"
            )

            return

        reward, activations = promo

        cursor = await db.execute("""
        SELECT *
        FROM promo_uses
        WHERE user_id = ? AND code = ?
        """, (user_id, code))

        used = await cursor.fetchone()

        if used is not None:

            await message.answer(
                "❌ Вы уже использовали этот промокод"
            )

            return

        await db.execute("""
        UPDATE users
        SET money = money + ?
        WHERE user_id = ?
        """, (reward, user_id))

        await db.execute("""
        INSERT INTO promo_uses
        (user_id, code)
        VALUES (?, ?)
        """, (user_id, code))

        activations -= 1

        if activations <= 0:

            await db.execute("""
            DELETE FROM promocodes
            WHERE code = ?
            """, (code,))

        else:

            await db.execute("""
            UPDATE promocodes
            SET activations = ?
            WHERE code = ?
            """, (activations, code))

        await db.commit()

    await message.answer(
        f"🎁 Промокод активирован!\n\n"
        f"+{reward} монет"
    )

# ================= TOP =================

@dp.callback_query(F.data == "top")
async def top(callback: CallbackQuery):

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
        SELECT user_id, money
        FROM users
        ORDER BY money DESC
        LIMIT 10
        """)

        users = await cursor.fetchall()

    text = "🏆 ТОП ИГРОКОВ\n\n"

    for i, user in enumerate(users, start=1):

        text += f"{i}. ID {user[0]} — {user[1]} 💰\n"

    await callback.message.edit_text(
        text,
        reply_markup=menu()
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

@dp.message(Command("pay"))
async def pay_command(message: Message):
    args = message.text.split()

    # Проверка формата команды
    if len(args) != 3:
        await message.answer(
            "❌ Использование:\n"
            "/pay ID сумма\n\n"
            "Пример:\n"
            "/pay 123456789 100000"
        )
        return

    # Проверяем ID
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID игрока.")
        return

    # Проверяем сумму
    try:
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ Сумма должна быть числом.")
        return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0.")
        return

    sender_id = message.from_user.id

    # Нельзя переводить самому себе
    if sender_id == target_id:
        await message.answer("❌ Нельзя переводить деньги самому себе.")
        return

    async with aiosqlite.connect(DB_PATH) as db:

        # Получаем баланс отправителя
        cursor = await db.execute(
            "SELECT money FROM users WHERE user_id = ?",
            (sender_id,)
        )
        sender = await cursor.fetchone()

        if not sender:
            await message.answer("❌ Ваш профиль не найден.")
            return

        sender_money = sender[0]

        # Проверяем баланс
        if sender_money < amount:
            await message.answer("❌ Недостаточно средств.")
            return

        # Проверяем существование получателя
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (target_id,)
        )
        target = await cursor.fetchone()

        if not target:
            await message.answer(
                "❌ Получатель не найден.\n"
                "Он должен хотя бы один раз запустить бота."
            )
            return

        # Списываем деньги у отправителя
        await db.execute(
            "UPDATE users SET money = money - ? WHERE user_id = ?",
            (amount, sender_id)
        )

        # Начисляем деньги получателю
        await db.execute(
            "UPDATE users SET money = money + ? WHERE user_id = ?",
            (amount, target_id)
        )

        await db.commit()

    # Сообщение отправителю
    await message.answer(
        f"✅ Вы успешно перевели {format_number(amount)} монет игроку `{target_id}`",
        parse_mode="Markdown"
    )

    # Уведомление получателю
    try:
        await bot.send_message(
            target_id,
            f"💸 Вам перевели {format_number(amount)} монет!"
        )
    except:
        pass
    
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

@dp.callback_query(F.data == "pay")
async def pay_button(callback: CallbackQuery):
    await callback.message.answer(
        "💸 Перевод денег\n\n"
        "Используйте команду:\n"
        "/pay ID сумма\n\n"
        "Пример:\n"
        "/pay 123456789 100000"
    )
    await callback.answer()

# ================= MAIN =================

async def main():

    await db_start()

    asyncio.create_task(auto_farm())

    print("Бот запущен")
    print(f"База данных: {DB_PATH}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
