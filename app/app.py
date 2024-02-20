from flask import Flask
from flask import render_template # Подключаем библиотеку для работы с шаблонами 
from flask import request # Для обработка запросов из форм
from flask import redirect # Для автоматического перенаправления 
import mysql.connector
import datetime # Для получения текущей даты и времени

app = Flask(__name__)


config = {
    'user': 'root',
    'password': 'root',
    'host': 'db',
    'port': '3306',
    'database': 'my_database'
}


def database_query(statement, data=None, is_change=False):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute(statement, data)
    result = []
    for row in cursor:
        result.append(dict(row))
    cursor.close()
    if is_change:
        connection.commit()
    else:
        connection.close()
    return result


@app.route("/") # Обрабатываем корневой путь
def main(): # Основная страница
#    return "<b>Hello</b> world!!!"
    all_users = get_all_users()
    return render_template('index.html', data=all_users)  # Вызываем шаблон main.html, в который в качестве data передано all_users


# Обрабатываем пути вида user/XXX, где XXX - user_id  
# Вызов страницы может быть методами с GET или POST
@app.route("/user/<int:user_id>", methods=['GET','POST'])
def user(user_id):

    if request.method == "POST": # Если были переданы данные из формы методом POST
        if 'delete_button' in request.form: # Если была нажата кнопка delete_button
            user_delete_all_messages(user_id) # То вызываем функцию удаления всех сообщений пользователя
        elif 'message_text' in request.form: # Если была нажата кнопка отправки текста 
            if len(request.form['message_text']) > 0: #Если текст был введен
                add_message(user_id, request.form['message_text']) # Вызываем функцию записи данных
        return redirect('/user/'+str(user_id)) # Необходимо еще раз перейти на эту страницу, но уже без вызова меода POST
        

    user_info = get_user_info(user_id) # Получить информацию о пользователей
    user_messages = get_user_messages(user_id) # Получить все сообщения пользователя
    
    user_subscriptions = get_user_subscription(user_id) # Получить ID всех подписок пользователя 
    user_subscriptions_info = [] #
    
    for sub in user_subscriptions:
        subscription_id = sub['user2_id']
        user_subscriptions_info.append(get_user_info(subscription_id))
        
    return render_template('user.html', 
                                        user=user_info, 
                                        messages=user_messages, 
                                        subscriptions=user_subscriptions_info, 
                          )
    
    
@app.route("/subscriptions/", methods=['GET'])
def subscriptions():
    info_message = None # Это сообщение будет выводиться только если произошло какое-то действие
    if request.args.get('action') == "delete": # Если в адресной строке есть action=delete
        user1_id = request.args.get('user1_id') # Получаем значение user1_id из адресной строки
        user2_id = request.args.get('user2_id') # Получаем значение user1_id из адресной строки
        result = delete_subscription(user1_id, user2_id) # Вызываем функцию для удаления строк в таблице подписок и получаем результат (количество обработанных строк)
        if result: #Если строк != 0
            info_message = "Delete subscription user1_id=" + user1_id + ", user1_id=" + user2_id # то готовим текст сообщения, что было удаление
    
    elif request.args.get('action') == "add": # Если в адресной строке есть action=add
        user1_id = request.args.get('user1_id') # Получаем значение user1_id из адресной строки
        user2_id = request.args.get('user2_id') # Получаем значение user1_id из адресной строки
        add_subscription(user1_id, user2_id) # Вызываем функцию для добавления строи в таблицу подписок
        info_message = "Add subscription user1_id=" + user1_id + ", user1_id=" + user2_id # готовим текст, что было добавление

    
    user_subscriptions = get_all_subscriptions() # Загружаем список всех подписок. Одна подписка хранится в виде словаря с указанием только ID пользователя 
    user_subscriptions_table = [] # Сформируем список всех подписок с именами пользователей
    for row in user_subscriptions:
        # Для каждой подписки получаем имена соответствующих пользователей 
        user1_info = get_user_info(row['user1_id'])
        user2_info = get_user_info(row['user2_id'])
        user_subscriptions_table.append(
            {
                'user1_id' : row['user1_id'],
                'user1_name': user1_info['name'],
                'user2_id' : row['user2_id'],
                'user2_name': user2_info['name'],            
            }        
        )
    
    all_users = get_all_users() # Загружаем список всех пользователей. Потребуется для создания селекторов в новых подписках
    return render_template('subscriptions.html',
                            subscriptions=user_subscriptions_table,
                            users=all_users,
                            message=info_message)


def get_user_info(user_id): # Получить информацию о пользователе по user_id
    user = database_query('SELECT * FROM user WHERE id=%s', (user_id,))
    return user[0]

def get_all_users(): # Получить список информации о всех пользователях 
    all_users = database_query('SELECT * FROM user')
    return all_users

def get_user_messages(user_id): # Получить все сообщения пользователя user_id
    messages = database_query('SELECT * FROM message WHERE user_id=%s ORDER BY time DESC', (user_id,))
    return messages

def user_delete_all_messages(user_id): # Удалить все сообщения пользователя user_id
    database_query('DELETE FROM message WHERE user_id=%s', (user_id,), True)
    return

def get_user_subscription(user_id): #Получить список всех подписок пользователя
    subscriptions = database_query('SELECT * FROM subscription WHERE user1_id=%s', (user_id,))
    return subscriptions    

def add_message(user_id, message_text): # Сохранить сообщение пользователя в базу
	current_time = datetime.datetime.now() # Получаем текущие дату и время 
	database_query('INSERT INTO message(user_id, text, time) VALUES (%s, %s, %s)', (user_id, message_text, current_time), True)
	return
    
def get_all_subscriptions(): # Получить все подписки 
    subscriptions = database_query('SELECT * FROM subscription')
    return subscriptions   
    
def delete_subscription(user1_id, user2_id): # Удалить заданную подписку
    database_query('DELETE FROM subscription WHERE user1_id=%s AND user2_id=%s', (user1_id, user2_id), True)
    return

def add_subscription(user1_id, user2_id): # Добавить новую подписку
    database_query('INSERT INTO subscription(user1_id, user2_id) VALUES (%s, %s)', (user1_id, user2_id), True)
    return

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0')