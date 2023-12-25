from backend import app,db
from datetime import datetime
import requests


class RoomSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    user = db.relationship('User', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    google_id = db.Column(db.String(100))
    session_id = db.Column(db.String(100))
    token = db.Column(db.String(1000))
    google_token = db.Column(db.String(1000))
    name = db.Column(db.String(100))
    nama_panggilan = db.Column(db.String(50))
    email = db.Column(db.String(100))
    no_telpon = db.Column(db.String(30))
    image_picture = db.Column(db.String(1000))
    jurusan = db.Column(db.String(100))
    universitas = db.Column(db.String(100))
    is_on_stream = db.Column(db.Boolean,default=False)
    verified_account = db.Column(db.Boolean,default=False)
    premium_status = db.Column(db.DateTime)
    transaction = db.relationship('Transaction',lazy=True)
    room_session = db.Column(db.Integer, db.ForeignKey('room_session.id'))
    def get_json(self):
        return {'name':self.name.title(),'short_name':self.nama_panggilan,'token':self.token,'picture':self.image_picture,'no_telpon':self.no_telpon,'jurusan':self.jurusan,'universitas':self.universitas,'verified_account':self.verified_account,'phone':self.no_telpon}
    
    def get_all_json(self):
        return {
            'google_id':self.google_id,
            'session_id':self.session_id,
            'token':self.token,
            'google_token':self.google_token,
            'name':self.name,
            'nama_panggilan':self.nama_panggilan,
            'email':self.email,
            'no_telpon':self.no_telpon,
            'image_picture':self.image_picture,
            'jurusan':self.jurusan,
            'universitas':self.universitas,
            'is_on_stream':self.is_on_stream,
            'verified_account':self.verified_account,
            'premium_status':self.premium_status,
            'room_session':self.room_session,
            'transaction':self.transaction
        }


class PromoCode(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    code = db.Column(db.String(100))
    discount = db.Column(db.Integer)

class Transaction(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    transaction_id = db.Column(db.String(100))
    jenis = db.Column(db.String(100))
    subscribe_time = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    tax = db.Column(db.Integer)
    total_amount = db.Column(db.Integer)
    transactionid = db.Column(db.String(200))
    paymentchannel = db.Column(db.String(100))
    paymentno = db.Column(db.String(500))
    status = db.Column(db.String(100))
    notify_url = db.Column(db.String(300))
    user = db.Column(db.Integer,db.ForeignKey('user.id'))