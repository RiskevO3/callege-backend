from backend import app, socketio
from backend.controller import \
    login_authentication,\
    logout_acc,\
    update_acc,\
    google_login_handler,\
    refresh_transaction,\
    validate_promo_code,\
    get_access_room_token,\
    get_room_name,\
    twilio_callback_handler,\
    make_transaction,\
    callback_payment

from flask_socketio import emit,join_room,leave_room
from json import loads
from flask import request


@app.route('/')
def index():
    return 'Hello World',200


@app.route('/updateaccount',methods=['POST'])
def update_account():
    data = loads(request.data.decode('utf-8'))
    token = data['token']
    short_name = data['shortName']
    phone = data['phone']
    return update_acc(token=token,short_name=short_name,phone=phone)

@app.route('/googlelogin',methods=['POST'])
def google_login_route():
    code = loads(request.data.decode('utf-8'))['code']
    print(code,'dari code broooo')
    return google_login_handler(code=code)

@app.route("/logout",methods=['POST'])
def logout():
    token = loads(request.data.decode('utf-8'))['token']
    return logout_acc(token=token)

@app.route("/auth",methods=['POST'])
def auth():
    token = loads(request.data.decode('utf-8'))['token']
    return login_authentication(token=token)

# bagian baru
@app.route('/generateroomtoken',methods=['POST'])
def generate_room_token():
    data = loads(request.data.decode('utf-8'))
    session_token = data['session_token']
    room_token = data['room_token']
    return get_access_room_token(session_token=session_token,room_token=room_token)

@app.route('/getroomsession',methods=['POST'])
def get_room_session():
    data = loads(request.data.decode('utf-8'))
    session_token = data['session_token']
    room_token = data['room_token']
    return get_room_name(session_token=session_token,room_token=room_token)

@app.route('/twilliotest',methods=['POST'])
def twillio_test():
    twilio_dict = request.form.to_dict()
    print('============dari twilio global callback=============')
    print(twilio_dict)
    print('==================================================')
    return twilio_callback_handler(twilio_dict=twilio_dict)
# ===========

@app.route('/maketransaction',methods=['POST'])
def make_transaction_route():
    data = loads(request.data.decode('utf-8'))
    token = data['token']
    promo_code = data['promo_code']
    total_price = int(data['total_price'])
    subscribe_time = int(data['subscribe_time'])
    payment_channel = data['payment_channel']
    return make_transaction(token=token,promo_code=promo_code,total_price=total_price,subscribe_time=subscribe_time,payment_channel=payment_channel)

@app.route('/callbackpayment',methods=['POST'])
def callback_test():
    callback_dict = request.form.to_dict()
    print('============dari callback test=============')
    print(callback_dict)
    if callback_dict['status_code'] == '1':
        print('iya bro masuk juga')
    print('==========================================')
    return callback_payment(dict=callback_dict)

@app.route('/promocodeverification',methods=['POST'])
def request_promocode():
    promo_code = loads(request.data.decode('utf-8'))['promo_code']
    return validate_promo_code(promo_code=promo_code)

@app.route('/refreshpaymentstatus',methods=['POST'])
def refresh_payment_route():
    data = loads(request.data.decode('utf-8'))
    token = data['token']
    transaction_id = data['transaction_id']
    return refresh_transaction(token=token,trxid=transaction_id)



# soon deleted

# @app.route('/generateloginurl',methods=['POST'])
# def generate_login_url():
#     return gen_login()

# @app.route('/createuser',methods=['POST'])
# def create_user_sess():
#     session_id = loads(request.data.decode('utf-8'))['session_id']
#     return create_user_session(session_id=session_id)

# @app.route('/generatetoken',methods=['POST'])
# def generate_token():
#     session_id = loads(request.data.decode('utf-8'))['session_id']
#     return get_access_videoroom_token(user_session_id=session_id)

# @app.route('/endcall',methods=['POST'])
# def end_call():
#     room_name = loads(request.data.decode('utf-8'))['room_name']
#     user_sess = loads(request.data.decode('utf-8'))['user_sess']
#     return {'success':end_room_session(room_name=room_name,user_sess=user_sess)},200

@socketio.on('connect',namespace='/socket')
def onconnect():
    print('user has been connectedd')
    emit('connect', {'data': 'Connected'})

@socketio.on('joinRoom',namespace='/socket')
def join_room_socket(msg):
    print('ini dari joinRoom')
    print(msg)
    print('===============')
    room = msg['room_session'] if type(msg) == type({}) else None
    if room:
        print(room)
        join_room(room)
        emit('joinRoomStatus',{'status':True,'message':f'join room {room} success!.'},room=room)
        print('join room success')


@socketio.on("leaveRoom",namespace='/socket')
def leave_room_socket(msg):
    room = msg['room_session']
    leave_room(room)
    emit('leaveRoomStatus',{'status':True,'message':f'leave room {room} success!.'})
    print('leave room success')
    
@socketio.on('sendmessage',namespace='/socket')
def send_message(msg):
    print(msg)
    emit('message',{'message':msg['message'],'from':msg['sessionId'],'sendername':msg['senderName']},namespace='/socket',room=msg['room'])