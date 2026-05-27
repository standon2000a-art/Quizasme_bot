import telebot
from telebot import types
import sqlite3
import random

# --- API TOKENINGIZNI SHU YERGA YOZING ---
API_TOKEN = '8834331837:AAEtPHAwWtZwGz27l5nC_cs0hgneHCPGoSQ'
bot = telebot.TeleBot(API_TOKEN)

# Bazani sozlashinit_db()
def init_db():
    conn = sqlite3.connect('users_data.db')
    cursor = conn.cursor()
    # Jadvalni yangi ustunlar bilan qayta yaratish uchun avvalgisini o'chirib tashlaymiz
    cursor.execute('DROP TABLE IF EXISTS questions')
    cursor.execute('''CREATE TABLE questions 
                      (user_id INTEGER, question TEXT, answer TEXT)''')
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('/add_question'), types.KeyboardButton('/play'))
    markup.add(types.KeyboardButton('/my_vocabulary'), types.KeyboardButton('/delete_questions'))
    markup.add(types.KeyboardButton('/stats'))
    bot.send_message(message.chat.id, "Salom! Men sizning shaxsiy o'quv botingizman. Savollarni qo'shing va o'yinni boshlang!", reply_markup=markup)

@bot.message_handler(commands=['add_question'])
def add_question(message):
    msg = bot.send_message(message.chat.id, "Savolni yozing:")
    bot.register_next_step_handler(msg, get_answer)

def get_answer(message):
    question = message.text
    msg = bot.send_message(message.chat.id, "Javobni yozing:")
    bot.register_next_step_handler(msg, save_to_db, question)

def save_to_db(message, question):
    answer = message.text
    conn = sqlite3.connect('users_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (user_id, question, answer) VALUES (?, ?, ?)", 
                   (message.chat.id, question, answer))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ Saqlandi!")

@bot.message_handler(commands=['play'])
def play(message):
    conn = sqlite3.connect('users_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM questions WHERE user_id = ?", (message.chat.id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(message.chat.id, "Bazangiz bo'sh. Avval savol qo'shing!")
        return
    
    total = len(rows)
    limit = max(1, total - 5)
    selected_questions = random.sample(rows, limit)
    
    bot.send_message(message.chat.id, f"🎮 O'yin boshlandi! Jami {total} ta savolingiz bor, {limit} tasini o'ynaymiz.")
    send_game_questions(message, selected_questions, 0, 0)

def send_game_questions(message, questions, index, score):
    if index < len(questions):
        q, a = questions[index]
        msg = bot.send_message(message.chat.id, f"Savol {index+1}/{len(questions)}: {q}")
        bot.register_next_step_handler(msg, check_game_answer, questions, index, score, a)
    else:
        bot.send_message(message.chat.id, f"🏁 O'yin tugadi! Siz {score} ta to'g'ri javob berdingiz!")

def check_game_answer(message, questions, index, score, correct_answer):
    if message.text.strip().lower() == correct_answer.lower():
        bot.send_message(message.chat.id, "✅ To'g'ri!")
        score += 1
    else:
        bot.send_message(message.chat.id, f"❌ Xato. To'g'ri javob: {correct_answer}")
    send_game_questions(message, questions, index + 1, score)

@bot.message_handler(commands=['my_vocabulary'])
def show_vocabulary(message):
    conn = sqlite3.connect('users_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM questions WHERE user_id = ?", (message.chat.id,))
    rows = cursor.fetchall()
    conn.close()
    if rows:
        resp = "📖 **Sizning savollaringiz:**\n\n" + "\n".join([f"{i}. {r[0]} - {r[1]}" for i, r in enumerate(rows, 1)])
        bot.send_message(message.chat.id, resp, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Lug'at bo'sh.")

@bot.message_handler(commands=['delete_questions'])
def delete_questions(message):
    conn = sqlite3.connect('users_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE user_id = ?", (message.chat.id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "🗑 Hammasi o'chirildi.")

@bot.message_handler(commands=['stats'])
def stats(message):
    conn = sqlite3.connect('users_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM questions")
    count = cursor.fetchone()[0]
    bot.send_message(message.chat.id, f"📊 Foydalanuvchilar: {count}")
    conn.close()

bot.infinity_polling()
