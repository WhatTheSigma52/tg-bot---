import telebot
from telebot import types
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta


load_dotenv()
TOKEN = os.getenv('TOKEN')


bot = telebot.TeleBot(TOKEN)


SCHEDULE = ["10:00", "12:00", "15:00", "17:00"]


def opening_json():
    '''Load JSON-file to dict.'''
    with open('data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def closing_json(data):
    '''Write new data in JSON-file.'''
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def add_appointment(user_date, user_time, user_client):
    '''Add new appointment in JSON-file.'''
    data = opening_json()
    data['appointments'].append({"date": user_date,
                                 "time": user_time,
                                 "client": user_client})
    closing_json(data)


def time_keyboard(date):
    '''Return available time keyboard.'''
    reg_time = SCHEDULE
    data = opening_json()
    for app in data['appointments']:
        if app['date'] == date:
            if app['time'] in reg_time:
                reg_time.remove(app['time'])
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i in reg_time:
        markup.add(types.InlineKeyboardButton(
            text=i,
            callback_data=f'appointment;{date};{i}'))
    return markup


def delete_app(time, date, client):
    '''Delete specific appointment in JSON-file.'''
    data = opening_json()
    for i in data['appointments']:
        if i['time'] == time and i['date'] == date and i['client'] == client:
            data['appointments'].remove(i)
            closing_json(data)


def save_client(message):
    '''Save client's name in JSON-file.'''
    data = opening_json()
    data['clients'].append({f'{message.chat.id}': f'{message.text}'})
    closing_json(data)
    bot.send_message(message.chat.id, 'Ваше имя сохранено')


def review(message):
    '''Add client's reviews in JSON-file'''
    data = opening_json()
    data['reviews'].append({f'{message.chat.id}': f'{message.text}'})
    closing_json(data)
    bot.send_message(message.chat.id, 'Отзыв отправлен')


@bot.message_handler(commands=['add_review'])
def add_review(message):
    '''Ask client for review.'''
    bot.send_message(message.chat.id, 'Напишите отзыв:')
    bot.register_next_step_handler_by_chat_id(message.chat.id,
                                              lambda message: review(message))


@bot.message_handler(commands=['set_name'])
def set_name(message):
    '''Ask client for name.'''
    bot.send_message(message.chat.id, 'Введите ваше имя:')
    bot.register_next_step_handler_by_chat_id(message.chat.id,
                                              lambda message:
                                              save_client(message))


@bot.message_handler(commands=['change_appointment'])
def change_appointment(message):
    '''Show client's appointments.'''
    user_lst = []
    data = opening_json()
    for i in data['appointments']:
        if i['client'] == message.chat.id:
            user_lst.append(f'{i['date']};{i['time']}')
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i in user_lst:
        markup.add(types.InlineKeyboardButton(text=i,
                                              callback_data=f'chng_app;{i}'))
    if user_lst:
        bot.send_message(message.chat.id,
                         'Выберите запись:',
                         reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
                         'У вас нет записей. Записаться можно по команде: '
                         '/make_appointment')


@bot.message_handler(commands=['make_appointment'])
def make_appointment(message):
    '''Make appointment and save in JSON-data.'''
    dates_lst = []
    for i in range(7):
        date = datetime.now() + timedelta(days=(i + 3))
        date = date.strftime("%d-%m-%Y")
        dates_lst.append(date)
    data = opening_json()
    for date in dates_lst:
        count = 0
        for i in data['appointments']:
            if i['date'] == date:
                count += 1
            if count >= 4:
                dates_lst.remove(date)
                break
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i in dates_lst:
        markup.add(types.InlineKeyboardButton(text=i,
                                              callback_data=f'date;{i}'))
    bot.send_message(message.chat.id, 'Выберите день:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    '''Callback handler.'''
    if call.data.startswith('date;'):
        date = call.data.replace('date;', "")
        bot.send_message(call.message.chat.id,
                         'Выберите время:',
                         reply_markup=time_keyboard(date))
        bot.delete_message(call.message.chat.id,
                           call.message.message_id)
    if call.data.startswith('appointment;'):
        _, date, time = call.data.split(';')
        bot.send_message(call.message.chat.id,
                         f'Вы выбрали запись на: {date}; {time}')
        add_appointment(date, time, call.message.chat.id)
        bot.delete_message(call.message.chat.id,
                           call.message.message_id)
    if call.data.startswith('chng_app;'):
        _, date, time = call.data.split(';')
        delete_app(time, date, call.message.chat.id)
        bot.send_message(call.message.chat.id,
                         f'Запись на {time}; {date} удалена')


bot.polling(non_stop=True)
