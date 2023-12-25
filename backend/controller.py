from backend.models import app,db,RoomSession,User,PromoCode,Transaction
from backend import flow,twillio_client,socketio
import random,string
import twilio.jwt.access_token
import twilio.jwt.access_token.grants
from backend import jwt
from flask import redirect,url_for
from testdikti import dikti_search
import requests
import json,hashlib,hmac
from datetime import datetime,timedelta
import traceback
import time
import pytz


def generate_random_string(obj):
    characters = string.ascii_letters + string.digits
    while True:
        random_string = ''.join(random.choice(characters) for _ in range(5))
        res = obj.query.filter_by(session_id=random_string).first()
        if not res:
            return random_string

def generate_jwt(val):
    val_jwt = jwt.encode(val,app.config['SECRET_KEY'],algorithm='HS256')
    return val_jwt

def validate_jwt(val,secret_key=app.config['SECRET_KEY']):
    try:
        val_jwt = jwt.decode(val,secret_key,algorithms=['HS256'])
        return val_jwt
    except Exception as e:
        return False

# checking room token
def is_valid(times):
    current_time = time.time() + 7*3600  # WIB offset: 7 hours ahead of UTC
    expiration_time = int(times)
    if current_time > expiration_time:
        return False
    print('room token masi idup')
    return True

# core function room
def get_room():
    room_sessions = RoomSession.query.all()
    roomall = sorted(room_sessions, key=lambda rs: len(rs.user) > 2)
    print('ini room yang ada: ',[room.user for room in roomall])
    room = [room for room in roomall if room and 0 < len(room.user) < 2]
    print('ini room after filter: ',[roomi.user for roomi in room])
    if not room:
        room =RoomSession(session_id=generate_random_string(RoomSession))
        db.session.add(room)
        db.session.commit()
        room = [room]
        print('ini room baru dibuat:',room)
    return room[0]

def get_access_room_token(session_token,room_token=None):
    user = User.query.filter_by(token=session_token).first()
    temp_room_token = validate_jwt(room_token,secret_key=app.config['TWILIO_API_KEY_SECRET']) if room_token else None
    if user.room_session:
        user.room_session = None
        db.session.commit()
    if user:
        if temp_room_token and is_valid(temp_room_token['exp']):
            return {'roomToken':room_token,'success':True},200
        access_token = twilio.jwt.access_token.AccessToken(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_API_KEY_SID'], app.config['TWILIO_API_KEY_SECRET'], identity=user.session_id,ttl=86400)
        video_grant = twilio.jwt.access_token.grants.VideoGrant(room='')
        access_token.add_grant(video_grant)
        return {'roomToken':access_token.to_jwt(),'success':True},200
    return {'success':False},200

def get_room_name(session_token,room_token):
    user = User.query.filter_by(token=session_token).first()
    if user.room_session:
        user.room_session = None
        db.session.commit()
    room_token = validate_jwt(room_token,secret_key=app.config['TWILIO_API_KEY_SECRET'])
    if user and room_token:
        room_token = room_token if is_valid(room_token['exp']) else get_access_room_token(session_token=session_token)[0]['roomToken']
        room = get_room()
        room = room if room else False
        if room:
            user.room_session = room.id
            db.session.commit()
            return {'room_name':room.session_id,'roomToken':room_token,'success':True},200
    return {'success':False},200

def room_check(room_session_id):
    room = RoomSession.query.filter_by(session_id=room_session_id).first()
    if room and len(room.user) == 2:
        return True
    return False

def twilio_callback_handler(twilio_dict):
    if twilio_dict.get('ParticipantStatus') == 'disconnected':
        user_identity = twilio_dict.get('ParticipantIdentity')
        user = User.query.filter_by(session_id=user_identity).first()
        user.room_session = None
        db.session.commit()
        print(twilio_dict)
        participants = twillio_client.video \
                     .v1 \
                     .rooms(twilio_dict['RoomName']) \
                     .participants \
                     .list(status='connected', limit=2)
        print('list participant yang connect:',participants)
        if not participants:
            room = RoomSession.query.filter_by(session_id=twilio_dict['RoomName']).first()
            if room:
                db.session.delete(room)
                db.session.commit()
                try:
                    twillio_client.video.v1.rooms(twilio_dict['RoomName']).update(status='completed')
                except:
                    pass
                finally:
                    print('room sudah dihapus')
    return {'success':True},200

# login and authentication
def verify_data_mahasiswa(nama,email):
    pass

def update_acc(token,short_name,phone):
    user = User.query.filter_by(token=token).first()
    if user and short_name and phone:
        user.nama_panggilan = short_name
        user.no_telpon = phone
        user.verified_account = True
        db.session.commit()
        return {'success':True},200
    return {'success':False},200

def login_authentication(token):
    user = User.query.filter_by(token=token).first()
    if user:
        return {
            'success':True,
            'is_premium':user.premium_status,
            'name':user.name.title(),
            'picture':user.image_picture,
            'session_id':user.session_id,
            'email':user.email,
            'short_name':user.nama_panggilan if user.nama_panggilan else user.name.split(' ')[1].title(),
            'verified_account':user.verified_account,'phone':user.no_telpon if user.no_telpon else '',
            'universitas':user.universitas,'jurusan':user.jurusan
            },200
    return {'success':False},200

def revoke_token(access_token):
    revoke_url = f'https://accounts.google.com/o/oauth2/revoke?token={access_token}'
    response = requests.get(revoke_url)
    return True

def logout_acc(token):
    user = User.query.filter_by(token=token).first()
    if user:
        revoke_status = revoke_token(user.google_token)
        if revoke_status:
            user.session_id = generate_random_string(obj=User)
            user.token = generate_jwt({'session_id':user.session_id})
            user.google_token = None
            db.session.commit()
            return {'success':True},200
        return {'success':False},200
    
def input_google_data(data_json,session_id,google_token):
    try:
        user = User.query.filter_by(google_id=data_json['id']).first()
        if user:
            if user.session_id != session_id:
                # print('kesini bang')
                user.session_id = session_id
                user.token = generate_jwt({'session_id':user.session_id})
            user.google_token = google_token
            db.session.commit()
        elif not user:
            print(data_json)
            dikti_res = dikti_search(nama_mahasiswa=data_json['name'],email_mahasiswa=data_json['email'])
            if not dikti_res:
                return False
            user = User(
                session_id=session_id,
                google_id=data_json['id'],
                token = generate_jwt({'session_id':session_id}),
                google_token = google_token,
                name=data_json['name'].title(),
                nama_panggilan=data_json['given_name'].title(),
                email=data_json['email'],
                image_picture=data_json['picture'],
                jurusan=dikti_res['prodi'],
                universitas=dikti_res['univ']
                )
            db.session.add(user)
            db.session.commit()
            return user.get_json()
        return user.get_json()
    except:
        traceback.print_exc()
        return False

def verify_code(code):
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        access_token = credentials.token
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo',headers=headers)
        userinfo = userinfo_response.json()
        userinfo['access_token'] = access_token
        return userinfo
    except Exception:
        traceback.print_exc()
        return False

def google_login_handler(code):
    try:
        user_info = verify_code(code=code)
        if user_info:
            session_id = generate_random_string(obj=User)
            user = input_google_data(data_json=user_info,session_id=session_id,google_token=user_info['access_token'])
            print(user)
            if user:
                return {'success':True,'data':user},200
            return {'success':False},200
    except:
        traceback.print_exc()
        return {'success':False},200

# bagian payment
def generate_transaction_id():
    while True:
        trxid = 'CLG'+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        searchtrxid = Transaction.query.filter_by(transaction_id=trxid).first()
        if not searchtrxid:
            return trxid

def generatesign(body):
    data_body = json.dumps(body, separators=(',', ':'))
    encrypt_body = hashlib.sha256(data_body.encode()).hexdigest()
    string_to_sign = f"POST:{app.config['ipaymuva']}:{encrypt_body}:{app.config['ipaymukey']}"
    signature = hmac.new(app.config['ipaymukey'].encode(), string_to_sign.encode(), hashlib.sha256).hexdigest().lower()
    timestamp = datetime.today().strftime('%Y%m%d%H%M%S')
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'signature': signature,
        'va': app.config['ipaymuva'],
        'timestamp': timestamp
    }
    return data_body,headers

def createtrx(transaction):            
    ipaymu_url = "https://sandbox.ipaymu.com/api/v2/payment/direct"
    user = User.query.filter_by(id=transaction.user).first() 
    name = user.name
    phone = user.no_telpon
    email = user.email
    body = {
        'name': f'{name}',
        'phone': f'{phone}',
        'email': f'{email}',
        'amount': f'{transaction.total_amount}',
        'notifyUrl': f'{transaction.notify_url}',
        'expired': '24',
        'expiredType': 'hours',
        'comments': f'{transaction.transaction_id}',
        'paymentMethod': 'va' if transaction.paymentchannel != 'qris' else transaction.paymentchannel,
        'referenceId': f'{transaction.transaction_id}',
        'paymentChannel': transaction.paymentchannel
    }
    data_body,headers = generatesign(body)
    print(data_body)
    response = requests.post(ipaymu_url, headers=headers, data=data_body)
    print(response.json())
    if response.status_code == 200:
        response = response.json()
        transaction.transactionid = response['Data']['TransactionId']
        transaction.paymentno = response['Data']['PaymentNo']
        transaction.total_amount = response['Data']['SubTotal']
        transaction.tax = response['Data']['Fee']
        db.session.commit()
        return True
    return False

def make_transaction(token,payment_channel,promo_code,total_price,subscribe_time):
    user = User.query.filter_by(token=token).first()
    if user:
        promo_total = validate_promo_code(promo_code)[0]['discount']
        total_price = int(total_price) - promo_total
        timezone = pytz.timezone('Asia/Bangkok')
        time = subscribe_time * 30
        subtime = datetime.now(timezone) + timedelta(days=time)
        print('ini waktu subscribe:',subtime)
        transaction = Transaction(
            transaction_id=generate_transaction_id(),
            jenis='subscribe',
            subscribe_time=subscribe_time,
            amount=total_price,
            tax=0,
            total_amount=total_price,
            paymentchannel=payment_channel,
            user=user.id,
            status='pending',
            notify_url=f'{app.config["APP_URL"]}/callbackpayment'
        )
        db.session.add(transaction)
        db.session.commit()
        push_transaction = createtrx(transaction=transaction)
        if push_transaction:
            return {
                'success':True,
                'transactionId':transaction.transaction_id,
                'paymentNo':transaction.paymentno,
                'paymentChannel':transaction.paymentchannel,
                'totalAmount':transaction.total_amount,
                'callbackurl':transaction.notify_url,
                },200

def check_trx(trxid):
    url = "https://sandbox.ipaymu.com/api/v2/transaction"
    body={'transactionId': f'{trxid}'}
    data_body,headers = generatesign(body)
    response = requests.post(url, headers=headers, data=data_body)
    if response.status_code == 200:
        if response.json()['Data']['StatusDesc'] == 'Berhasil':
            return True
    return False

def validate_transaction(transaction):
    if transaction.status == 'success':
        return True
    user = User.query.filter_by(id=transaction.user).first()
    premium_status = datetime.now(pytz.timezone('Asia/Bangkok')) + timedelta(days=transaction.subscribe_time*30)
    transaction.status = 'success'
    user.premium_status  = premium_status if not user.premium_status else user.premium_status + timedelta(days=transaction.subscribe_time*30)
    db.session.commit()
    return True

def callback_payment(dict):
    if dict['status_code'] != '1':
        return {'success':False},200
    transaction = Transaction.query.filter_by(transaction_id=dict['reference_id']).first()
    if transaction:
        val_trx = validate_transaction(transaction=transaction)
        if val_trx:
            socketio.emit('paymentStatus',{'status':'success'},room=dict['reference_id'],namespace='/socket')
            return {'success':True},200
    return {'success':False},200

def validate_promo_code(promo_code):
    if not promo_code:
        return {'success':True,'discount':0},200
    promo_code = PromoCode.query.filter_by(code=promo_code).first()
    if promo_code:
        return {'success':True,'discount':promo_code.discount},200
    return {'success':False,'discount':0},200
    
def refresh_transaction(token,trxid):
    user = User.query.filter_by(token=token).first()
    if user:
        print('user valid')
        check_transaction = check_trx(trxid=trxid)
        if check_transaction:
            print('transaction sukses')
            transaction = Transaction.query.filter_by(transactionid=trxid).first()
            validate_trx = validate_transaction(transaction=transaction)
            if validate_trx:
                print('validate transaction sukses')
                return {'success':True},200
    return {'success':False},200

# debugging purpose
def reset_all_configuration():
    db.drop_all()
    db.create_all()
    room_list = get_all_room('in-progress')
    end_all_room_session(room_list)
    return 'success'

def get_all_room(status):
    rooms = twillio_client.video.v1.rooms.list(status=status, limit=20)
    print([room.unique_name for room in rooms])
    return [room.unique_name for room in rooms]

def end_all_room_session(list_room_name):
    for room_name in list_room_name:
        room_sess = RoomSession.query.filter_by(session_id=room_name).first()
        if room_sess:
            db.session.delete(room_sess)
            db.session.commit()
        room = twillio_client.video.v1.rooms(room_name).update(status='completed')
