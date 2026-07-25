from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aqualand.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Client(db.Model):
    __tablename__ = 'Clients'
    id_client = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(100), nullable=False)
    badge_rfid = db.Column(db.String(50), unique=True)
    minutes_restantes = db.Column(db.Integer, default=0)
    
    sessions = db.relationship('SessionPiscine', backref='client', lazy=True)
    paiements = db.relationship('Paiement', backref='client', lazy=True)
    
    def to_dict(self):
        return {
            'id_client': self.id_client,
            'nom': self.nom,
            'badge_rfid': self.badge_rfid,
            'minutes_restantes': self.minutes_restantes
        }

class SessionPiscine(db.Model):
    __tablename__ = 'SessionsPiscine'
    id_session = db.Column(db.Integer, primary_key=True, autoincrement=True)
    badge_rfid = db.Column(db.String(50), nullable=False)
    heure_entree = db.Column(db.DateTime, nullable=False, default=datetime.now)
    heure_sortie = db.Column(db.DateTime)
    minutes_consommees = db.Column(db.Integer)
    montant_paye = db.Column(db.Float, default=0.0)
    statut = db.Column(db.String(20), default='EN_COURS')
    
    def to_dict(self):
        return {
            'id_session': self.id_session,
            'badge_rfid': self.badge_rfid,
            'heure_entree': self.heure_entree.isoformat() if self.heure_entree else None,
            'heure_sortie': self.heure_sortie.isoformat() if self.heure_sortie else None,
            'minutes_consommees': self.minutes_consommees,
            'montant_paye': self.montant_paye,
            'statut': self.statut
        }

class Paiement(db.Model):
    __tablename__ = 'Paiements'
    id_paiement = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_client = db.Column(db.Integer, db.ForeignKey('Clients.id_client'), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    date_paiement = db.Column(db.DateTime, default=datetime.now)
    type_paiement = db.Column(db.String(20))
    
    def to_dict(self):
        return {
            'id_paiement': self.id_paiement,
            'id_client': self.id_client,
            'montant': self.montant,
            'date_paiement': self.date_paiement.isoformat(),
            'type_paiement': self.type_paiement
        }

class Tarif(db.Model):
    __tablename__ = 'Tarifs'
    id_tarif = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom_tarif = db.Column(db.String(100), nullable=False)
    prix_par_minute = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'id_tarif': self.id_tarif,
            'nom_tarif': self.nom_tarif,
            'prix_par_minute': self.prix_par_minute,
            'description': self.description
        }

# Routes - API
@app.route('/api/clients', methods=['GET', 'POST'])
def clients():
    if request.method == 'POST':
        data = request.get_json()
        new_client = Client(
            nom=data.get('nom'),
            badge_rfid=data.get('badge_rfid'),
            minutes_restantes=data.get('minutes_restantes', 0)
        )
        db.session.add(new_client)
        db.session.commit()
        return jsonify(new_client.to_dict()), 201
    
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients])

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'GET':
        return jsonify(client.to_dict())
    
    elif request.method == 'PUT':
        data = request.get_json()
        client.nom = data.get('nom', client.nom)
        client.minutes_restantes = data.get('minutes_restantes', client.minutes_restantes)
        db.session.commit()
        return jsonify(client.to_dict())
    
    elif request.method == 'DELETE':
        db.session.delete(client)
        db.session.commit()
        return '', 204

@app.route('/api/sessions', methods=['GET', 'POST'])
def sessions():
    if request.method == 'POST':
        data = request.get_json()
        new_session = SessionPiscine(
            badge_rfid=data.get('badge_rfid'),
            heure_entree=datetime.now()
        )
        db.session.add(new_session)
        db.session.commit()
        return jsonify(new_session.to_dict()), 201
    
    sessions = SessionPiscine.query.all()
    return jsonify([session.to_dict() for session in sessions])

@app.route('/api/sessions/<int:session_id>/checkout', methods=['POST'])
def checkout_session(session_id):
    session = SessionPiscine.query.get_or_404(session_id)
    data = request.get_json()
    
    session.heure_sortie = datetime.now()
    session.statut = 'TERMINE'
    
    # Calculate consumed minutes
    duration = (session.heure_sortie - session.heure_entree).total_seconds() / 60
    session.minutes_consommees = int(duration)
    
    # Calculate payment (placeholder - use tariff from request)
    tarif = data.get('prix_par_minute', 0.1)
    session.montant_paye = round(duration * tarif, 2)
    
    db.session.commit()
    return jsonify(session.to_dict())

@app.route('/api/sessions/active', methods=['GET'])
def active_sessions():
    active = SessionPiscine.query.filter_by(statut='EN_COURS').all()
    return jsonify([session.to_dict() for session in active])

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
