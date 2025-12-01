import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json
import os

# Твой токен
TOKEN = "8587938425:AAHJQLuJJfb8xM5sYqeS9niyZIvgF-C-lSg"

# Простая база в файле
DB_FILE = "users.db"

# 100 популярных интересов 2025 года
TAGS = [
    "#кино", "#музыка", "#путешествия", "#спорт", "#книги", "#аниме", "#игры", "#кулинария", "#фотография", "#танцы",
    "#йога", "#программирование", "#дизайн", "#психология", "#бизнес", "#стартапы", "#крипта", "#искусство", "#театр", "#поэзия",
    "#кошки", "#собаки", "#астрономия", "#настолки", "#косплей", "#тату", "#vegan", "#кофе", "#вино", "#пиво",
    "#горы", "#море", "#скейт", "#сноуборд", "#велосипед", "#авто", "#мото", "#рыбалка", "#охота", "#садоводство",
    "#медитация", "#мемы", "#standup", "#nft", "#ai", "#мода", "#минимализм", "#эзотерика", "#языки", "#корея",
    "#япония", "#скандинавия", "#берлин", "#бордерколли", "#шпиц", "#хаски", "#корги", "#аквариумистика", "#speedcubing",
    "#гитара", "#укулеле", "#винил", "#darkretreat", "#plantbased", "#кроссфит", "#калланетика", "#бокс", "#джиуджитсу"
]

user_data = {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except:
        user_data = {}

def compatibility(user1_tags, user2_tags):
    if not user1_tags or not user2_tags:
        return 0
    common = len(set(user1_tags) & set(user2_tags))
    total = len(set(user1_tags) | set(user2_tags))
    return common / total if total > 0 else 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Создать профиль", callback_data="create_profile")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Это #match — знакомства по настоящим интересам ❤️\n\n"
        "Выбери свои хэштеги, и я найду тебе самых похожих людей в Telegram!\n\n"
        "Нажми кнопку ниже ↓",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "create_profile":
        keyboard = []
        row = []
        for i, tag in enumerate(TAGS):
            row.append(InlineKeyboardButton(tag, callback_data=f"tag_{tag}"))
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("Готово", callback_data="done_tags")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выбери минимум 3 интереса (чем больше — тем точнее поиск):", reply_markup=reply_markup)

    elif query.data.startswith("tag_"):
        tag = query.data[4:]
        if user_id not in context.user_data:
            context.user_data[user_id] = {"tags": []}
        tags = context.user_data[user_id]["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)

        # перерисовка кнопок
        keyboard = []
        row = []
        for i, t in enumerate(TAGS):
            text = "✅ " + t if t in tags else t
            row.append(InlineKeyboardButton(text, callback_data=f"tag_{t}"))
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("Готово", callback_data="done_tags")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    elif query.data == "done_tags":
        selected_tags = context.user_data.get(user_id, {}).get("tags", [])
        if len(selected_tags) < 3:
            await query.edit_message_text("Выбери хотя бы 3 интереса!")
            return

        user_data[str(user_id)] = {
            "username": query.from_user.username or "",
            "first_name": query.from_user.first_name,
            "tags": selected_tags
        }
        save_db()
        await query.edit_message_text(
            f"Профиль готов! У тебя {len(selected_tags)} интересов!\n\n"
            f"{', '.join(selected_tags)}\n\n"
            "Теперь пиши /search — я найду тебе людей!",
        )

    elif query.data == "like":
        liker_id = context.user_data.get("current_user")
        liked_id = context.user_data.get("current_profile")

        # взаимный лайк?
        liker_liked = user_data.get(str(liker_id), {}).get("liked", [])
        if str(liked_id) in liker_liked:
            await query.edit_message_text(
                "ВЗАИМНЫЙ ЛАЙК! Напишите друг другу прямо сейчас ❤️\n\n"
                f"@{user_data.get(str(liked_id), {}).get('username', 'этот человек')}"
            )
            await context.bot.send_message(
                liked_id,
                "ВЗАИМНЫЙ ЛАЙК! Напишите друг другу прямо сейчас ❤️\n\n"
                f"@{query.from_user.username or query.from_user.first_name}"
            )
        else:
            await query.edit_message_text("Лайк отправлен ❤️")

        # сохраняем лайк
        if str(liker_id) not in user_data:
            user_data[str(liker_id)] = {}
        if "liked" not in user_data[str(liker_id)]:
            user_data[str(liker_id)]["liked"] = []
        user_data[str(liker_id)]["liked"].append(str(liked_id))
        save_db()

    elif query.data == "next":
        await search(update, context, edit=True)

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_id = update.callback_query.from_user.id if edit else update.effective_user.id

    if str(user_id) not in user_data:
        text = "Сначала создай профиль — жми /start"
        if edit:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return

    my_tags = set(user_data[str(user_id)]["tags"])
    candidates = []

    for uid, data in user_data.items():
        if uid == str(user_id):
            continue
        score = compatibility(my_tags, set(data["tags"]))
        if score > 0:
            candidates.append((score, uid, data))

    if not candidates:
        text = "Пока никого не нашёл. Добавь ещё тегов или подожди новых людей!"
        if edit:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return

    candidates.sort(reverse=True)
    score, found_id, found_data = candidates[0]
    percent = int(score * 100)

    keyboard = [
        [InlineKeyboardButton("❤️ Лайк", callback_data="like"),
         InlineKeyboardButton("➡️ Дальше", callback_data="next")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"Совместимость {percent}%\n\n" \
           f"👤 {found_data['first_name']} @{found_data.get('username', '')}\n" \
           f"Интересы: {', '.join(found_data['tags'])}"

    context.user_data["current_user"] = user_id
    context.user_data["current_profile"] = found_id

    if edit:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот #match запущен и работает 24/7!")
    app.run_polling()

if __name__ == '__main__':
    main()
  Initial bot code
