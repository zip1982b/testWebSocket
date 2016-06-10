# -*- coding: utf-8 -*-

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on available packages.
# thread
async_mode = 'eventlet'
import eventlet
eventlet.monkey_patch()

import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

values = {
    'slider1': 25,
    'slider2': 0,
}




def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(10)
        count += 1
        socketio.emit('Server response',
                      {'data': 'Server generated event and send to client', 'count': count},
                      namespace='/test1')
        socketio.emit('Server response',
                      {'data': 'Server generated event and send to client', 'count': count},
                      namespace='/test2')


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html', **values)



@socketio.on('value changed', namespace='/test1')
def value_changed(message):
    values[message['who']] = message['data']
    print(message['data'])
    emit('update value', message, broadcast=True)














# ************** Приём данных и их переотправка***********************************************
# принимает сообщения в формате {u'data': u'тут распологаются сами данные!'}
# 'server receives data' - название события
# namespace='/test' - позволяют клиенту открыть несколько подключений к серверу,
# который мультиплексированы на одном сокете. Если пространство имен не указано
# события привязаны к глобальному пространству имен по умолчанию.
@socketio.on('server receives data', namespace='/test1')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': message['data'], 'count': session['receive_count']})

@socketio.on('server receives data', namespace='/test2')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': message['data'], 'count': session['receive_count']})










# Получили сообщение от клиента
# и переотправили всем клиентам  broadcast=True
@socketio.on('my broadcast event', namespace='/test1')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)

# Получили сообщение от клиента
# и переотправили всем клиентам  broadcast=True
@socketio.on('my broadcast event', namespace='/test2')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test1')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test1')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})









@socketio.on('close room', namespace='/test1')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test1')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])

# *********** отключение клиента ************************************************
# Приняли запрос от клиента, на отключение
# отослали клиенту сообщение что он отключен
# и произвели отключение вызвав disconnect()
# вывели на сервере сообщение, что клиент отключен
@socketio.on('disconnect request', namespace='/test1')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('Server response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('disconnect', namespace='/test1')
def test_disconnect():
    print('Client disconnected', request.sid)
#*********************************************************************************

# **********отправка сообщения клиенту (в его namespace test1)что сервер подключен***************************************************
@socketio.on('connect', namespace='/test1')
def test_connect():
    emit('Server response', {'data': 'Server is Connected!', 'count': 0})
    print("Server is connected")


# **********отправка сообщения клиенту (в его namespace test2)что сервер подключен***************************************************
@socketio.on('connect', namespace='/test2')
def test_connect():
    emit('Server response', {'data': 'Server is Connected!', 'count': 0})
    print("Server is connected")

if __name__ == '__main__':
    socketio.run(app, debug=True)

