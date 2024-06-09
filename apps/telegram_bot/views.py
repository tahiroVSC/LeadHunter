from telebot import TeleBot, types
from apps.users.models import CustomUser

TELEGRAM_TOKEN = "7363032567:AAFUpwD19Hp_xB9v--O3ejfHbvOkmlLTFcI"

bot = TeleBot(TELEGRAM_TOKEN, threaded=False)

class UserState:
    def __init__(self):
        self.email = None
        self.user = None

user_states = {}

@bot.message_handler(commands=['start'])
def start(message: types.Message):
    bot.send_message(message.chat.id, "Привет! Для начала работы введите свой email.")
    bot.register_next_step_handler(message, ask_email)

def ask_email(message: types.Message):
    email = message.text
    try:
        user = CustomUser.objects.get(email=email)
        user_states[message.from_user.id] = UserState()
        user_states[message.from_user.id].email = email
        user_states[message.from_user.id].user = user
        bot.send_message(message.chat.id, f"Email {email} найден. Введите сумму для начисления на баланс.")
        bot.register_next_step_handler(message, ask_amount)
    except CustomUser.DoesNotExist:
        bot.send_message(message.chat.id, f"Email {email} не найден. Попробуйте снова.")
        bot.register_next_step_handler(message, ask_email)

def ask_amount(message: types.Message):
    try:
        amount = int(message.text)
        user_state = user_states.get(message.from_user.id)
        if user_state and user_state.user:
            user = user_state.user
            user.balance += amount
            user.save()
            bot.send_message(message.chat.id, f"Сумма {amount} успешно начислена на ваш баланс.")
        else:
            bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте снова.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную сумму.")
        bot.register_next_step_handler(message, ask_amount)

@bot.message_handler()
def echo(message: types.Message):
    bot.send_message(message.chat.id, "Я вас не понял")

if __name__ == '__main__':
    bot.polling(none_stop=True)
