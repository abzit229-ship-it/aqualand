from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps
import jwt
import hashlib

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aqualand.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)

# ============ MODELS ============

class User(db.Model):
    __tablename__ = 'Users'
    id_user = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'id_user': self.id_user,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Client(db.Model):
    __tablename__ = 'Clients'
    id_client = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(100), nullable=False)
    badge_rfid = db.Column(db.String(50), unique=True)
    minutes_restantes = db.Column(db.Integer, default=0)
    email = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    date_inscription = db.Column(db.DateTime, default=datetime.now)
    
    sessions = db.relationship('SessionPiscine', backref='client', lazy=True)
    paiements = db.relationship('Paiement', backref='client', lazy=True)
    
    def to_dict(self):
        return {
            'id_client': self.id_client,
            'nom': self.nom,
            'badge_rfid': self.badge_rfid,
            'minutes_restantes': self.minutes_restantes,
            'email': self.email,
            'telephone': self.telephone,
            'date_inscription': self.date_inscription.isoformat()
        }

class SessionPiscine(db.Model):
    __tablename__ = 'SessionsPiscine'
    id_session = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_client = db.Column(db.Integer, db.ForeignKey('Clients.id_client'))
    badge_rfid = db.Column(db.String(50), nullable=False)
    heure_entree = db.Column(db.DateTime, nullable=False, default=datetime.now)
    heure_sortie = db.Column(db.DateTime)
    minutes_consommees = db.Column(db.Integer)
    montant_paye = db.Column(db.Float, default=0.0)
    statut = db.Column(db.String(20), default='EN_COURS')
    prix_par_minute = db.Column(db.Float, default=0.10)
    
    def to_dict(self):
        return {
            'id_session': self.id_session,
            'id_client': self.id_client,
            'badge_rfid': self.badge_rfid,
            'heure_entree': self.heure_entree.isoformat() if self.heure_entree else None,
            'heure_sortie': self.heure_sortie.isoformat() if self.heure_sortie else None,
            'minutes_consommees': self.minutes_consommees,
            'montant_paye': self.montant_paye,
            'statut': self.statut,
            'prix_par_minute': self.prix_par_minute
        }

class Paiement(db.Model):
    __tablename__ = 'Paiements'
    id_paiement = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_client = db.Column(db.Integer, db.ForeignKey('Clients.id_client'), nullable=False)
    id_session = db.Column(db.Integer, db.ForeignKey('SessionsPiscine.id_session'))
    montant = db.Column(db.Float, nullable=False)
    date_paiement = db.Column(db.DateTime, default=datetime.now)
    type_paiement = db.Column(db.String(20))  # CASH, CARTE, CHEQUE
    description = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'id_paiement': self.id_paiement,
            'id_client': self.id_client,
            'id_session': self.id_session,
            'montant': self.montant,
            'date_paiement': self.date_paiement.isoformat(),
            'type_paiement': self.type_paiement,
            'description': self.description
        }

class Tarif(db.Model):
    __tablename__ = 'Tarifs'
    id_tarif = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom_tarif = db.Column(db.String(100), nullable=False)
    prix_par_minute = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    actif = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id_tarif': self.id_tarif,
            'nom_tarif': self.nom_tarif,
            'prix_par_minute': self.prix_par_minute,
            'description': self.description,
            'actif': self.actif
        }

# ============ AUTHENTICATION ============

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token invalide'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'message': 'Utilisateur existe déjà'}), 400
    
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        role=data.get('role', 'user')
    )
    user.set_password(data.get('password'))
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Utilisateur créé avec succès'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if not user or not user.check_password(data.get('password')):
        return jsonify({'message': 'Identifiants invalides'}), 401
    
    token = jwt.encode(
        {'user_id': user.id_user, 'exp': datetime.utcnow() + timedelta(hours=24)},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    }), 200

# ============ CLIENTS ROUTES ============

@app.route('/api/clients', methods=['GET', 'POST'])
def clients():
    if request.method == 'POST':
        data = request.get_json()
        
        if data.get('badge_rfid') and Client.query.filter_by(badge_rfid=data.get('badge_rfid')).first():
            return jsonify({'message': 'Badge RFID existe déjà'}), 400
        
        new_client = Client(
            nom=data.get('nom'),
            badge_rfid=data.get('badge_rfid'),
            email=data.get('email'),
            telephone=data.get('telephone'),
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
        client.email = data.get('email', client.email)
        client.telephone = data.get('telephone', client.telephone)
        client.minutes_restantes = data.get('minutes_restantes', client.minutes_restantes)
        db.session.commit()
        return jsonify(client.to_dict())
    
    elif request.method == 'DELETE':
        db.session.delete(client)
        db.session.commit()
        return '', 204

@app.route('/api/clients/search/<badge_rfid>', methods=['GET'])
def search_client_by_rfid(badge_rfid):
    client = Client.query.filter_by(badge_rfid=badge_rfid).first()
    if not client:
        return jsonify({'message': 'Client non trouvé'}), 404
    return jsonify(client.to_dict())

# ============ SESSIONS ROUTES ============

@app.route('/api/sessions', methods=['GET', 'POST'])
def sessions():
    if request.method == 'POST':
        data = request.get_json()
        
        client = Client.query.filter_by(badge_rfid=data.get('badge_rfid')).first()
        
        new_session = SessionPiscine(
            id_client=client.id_client if client else None,
            badge_rfid=data.get('badge_rfid'),
            heure_entree=datetime.now(),
            prix_par_minute=data.get('prix_par_minute', 0.10)
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
    
    duration = (session.heure_sortie - session.heure_entree).total_seconds() / 60
    session.minutes_consommees = int(duration)
    
    tarif = data.get('prix_par_minute', session.prix_par_minute)
    session.montant_paye = round(duration * tarif, 2)
    
    if session.id_client:
        paiement = Paiement(
            id_client=session.id_client,
            id_session=session_id,
            montant=session.montant_paye,
            type_paiement=data.get('type_paiement', 'CARTE'),
            description=f"Session {session_id}"
        )
        db.session.add(paiement)
        
        client = Client.query.get(session.id_client)
        if client:
            client.minutes_restantes -= session.minutes_consommees
    
    db.session.commit()
    return jsonify(session.to_dict())

@app.route('/api/sessions/active', methods=['GET'])
def active_sessions():
    active = SessionPiscine.query.filter_by(statut='EN_COURS').all()
    return jsonify([session.to_dict() for session in active])

@app.route('/api/sessions/statistics', methods=['GET'])
def session_statistics():
    today = datetime.now().date()
    today_sessions = SessionPiscine.query.filter(
        db.func.date(SessionPiscine.heure_entree) == today,
        SessionPiscine.statut == 'TERMINE'
    ).all()
    
    total_sessions = len(today_sessions)
    total_revenue = sum(s.montant_paye for s in today_sessions)
    total_minutes = sum(s.minutes_consommees or 0 for s in today_sessions)
    
    return jsonify({
        'date': today.isoformat(),
        'total_sessions': total_sessions,
        'total_revenue': round(total_revenue, 2),
        'total_minutes': total_minutes,
        'active_sessions': len(SessionPiscine.query.filter_by(statut='EN_COURS').all())
    })

# ============ TARIFS ROUTES ============

@app.route('/api/tarifs', methods=['GET', 'POST'])
def tarifs():
    if request.method == 'POST':
        data = request.get_json()
        new_tarif = Tarif(
            nom_tarif=data.get('nom_tarif'),
            prix_par_minute=data.get('prix_par_minute'),
            description=data.get('description')
        )
        db.session.add(new_tarif)
        db.session.commit()
        return jsonify(new_tarif.to_dict()), 201
    
    tarifs = Tarif.query.filter_by(actif=True).all()
    return jsonify([tarif.to_dict() for tarif in tarifs])

@app.route('/api/tarifs/<int:tarif_id>', methods=['GET', 'PUT', 'DELETE'])
def tarif_detail(tarif_id):
    tarif = Tarif.query.get_or_404(tarif_id)
    
    if request.method == 'GET':
        return jsonify(tarif.to_dict())
    
    elif request.method == 'PUT':
        data = request.get_json()
        tarif.nom_tarif = data.get('nom_tarif', tarif.nom_tarif)
        tarif.prix_par_minute = data.get('prix_par_minute', tarif.prix_par_minute)
        tarif.description = data.get('description', tarif.description)
        tarif.actif = data.get('actif', tarif.actif)
        db.session.commit()
        return jsonify(tarif.to_dict())
    
    elif request.method == 'DELETE':
        tarif.actif = False
        db.session.commit()
        return '', 204

# ============ PAIEMENTS ROUTES ============

@app.route('/api/paiements', methods=['GET', 'POST'])
def paiements():
    if request.method == 'POST':
        data = request.get_json()
        new_paiement = Paiement(
            id_client=data.get('id_client'),
            id_session=data.get('id_session'),
            montant=data.get('montant'),
            type_paiement=data.get('type_paiement'),
            description=data.get('description')
        )
        db.session.add(new_paiement)
        db.session.commit()
        return jsonify(new_paiement.to_dict()), 201
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    paiements = Paiement.query.order_by(Paiement.date_paiement.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return jsonify({
        'items': [p.to_dict() for p in paiements.items],
        'total': paiements.total,
        'pages': paiements.pages,
        'current_page': page
    })

@app.route('/api/paiements/client/<int:client_id>', methods=['GET'])
def client_paiements(client_id):
    paiements = Paiement.query.filter_by(id_client=client_id).order_by(
        Paiement.date_paiement.desc()
    ).all()
    return jsonify([p.to_dict() for p in paiements])

# ============ REPORTS ROUTES ============

@app.route('/api/rapports/daily', methods=['GET'])
def daily_report():
    today = datetime.now().date()
    
    sessions = SessionPiscine.query.filter(
        db.func.date(SessionPiscine.heure_entree) == today,
        SessionPiscine.statut == 'TERMINE'
    ).all()
    
    total_sessions = len(sessions)
    total_revenue = sum(s.montant_paye for s in sessions)
    total_minutes = sum(s.minutes_consommees or 0 for s in sessions)
    clients_count = len(set(s.id_client for s in sessions if s.id_client))
    
    rapport = {
        'date': today.isoformat(),
        'type': 'daily',
        'total_sessions': total_sessions,
        'total_revenue': round(total_revenue, 2),
        'total_minutes': total_minutes,
        'nombre_clients': clients_count
    }
    
    return jsonify(rapport)

@app.route('/api/rapports/weekly', methods=['GET'])
def weekly_report():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    sessions = SessionPiscine.query.filter(
        db.func.date(SessionPiscine.heure_entree) >= week_start,
        db.func.date(SessionPiscine.heure_entree) <= week_end,
        SessionPiscine.statut == 'TERMINE'
    ).all()
    
    total_sessions = len(sessions)
    total_revenue = sum(s.montant_paye for s in sessions)
    total_minutes = sum(s.minutes_consommees or 0 for s in sessions)
    clients_count = len(set(s.id_client for s in sessions if s.id_client))
    
    rapport = {
        'period': f"{week_start.isoformat()} to {week_end.isoformat()}",
        'type': 'weekly',
        'total_sessions': total_sessions,
        'total_revenue': round(total_revenue, 2),
        'total_minutes': total_minutes,
        'nombre_clients': clients_count
    }
    
    return jsonify(rapport)

@app.route('/api/rapports/monthly', methods=['GET'])
def monthly_report():
    today = datetime.now().date()
    month_start = today.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    sessions = SessionPiscine.query.filter(
        db.func.date(SessionPiscine.heure_entree) >= month_start,
        db.func.date(SessionPiscine.heure_entree) <= month_end,
        SessionPiscine.statut == 'TERMINE'
    ).all()
    
    total_sessions = len(sessions)
    total_revenue = sum(s.montant_paye for s in sessions)
    total_minutes = sum(s.minutes_consommees or 0 for s in sessions)
    clients_count = len(set(s.id_client for s in sessions if s.id_client))
    
    rapport = {
        'period': f"{month_start.isoformat()} to {month_end.isoformat()}",
        'type': 'monthly',
        'total_sessions': total_sessions,
        'total_revenue': round(total_revenue, 2),
        'total_minutes': total_minutes,
        'nombre_clients': clients_count
    }
    
    return jsonify(rapport)

# ============ ANALYTICS ROUTES ============

@app.route('/api/analytics/revenue-by-day', methods=['GET'])
def revenue_by_day():
    days = request.args.get('days', 7, type=int)
    start_date = datetime.now().date() - timedelta(days=days)
    
    sessions = SessionPiscine.query.filter(
        db.func.date(SessionPiscine.heure_entree) >= start_date,
        SessionPiscine.statut == 'TERMINE'
    ).all()
    
    revenue_by_day = {}
    for session in sessions:
        date_key = session.heure_entree.date().isoformat()
        revenue_by_day[date_key] = revenue_by_day.get(date_key, 0) + session.montant_paye
    
    return jsonify(revenue_by_day)

@app.route('/api/analytics/peak-hours', methods=['GET'])
def peak_hours():
    sessions = SessionPiscine.query.filter(
        SessionPiscine.statut == 'TERMINE'
    ).all()
    
    hour_usage = {}
    for session in sessions:
        hour = session.heure_entree.hour
        hour_usage[hour] = hour_usage.get(hour, 0) + 1
    
    return jsonify(hour_usage)

@app.route('/api/analytics/client-usage', methods=['GET'])
def client_usage():
    clients = Client.query.all()
    
    usage_data = []
    for client in clients:
        sessions = SessionPiscine.query.filter_by(id_client=client.id_client).all()
        total_minutes = sum(s.minutes_consommees or 0 for s in sessions)
        total_spent = sum(s.montant_paye for s in sessions)
        
        usage_data.append({
            'id_client': client.id_client,
            'nom': client.nom,
            'sessions_count': len(sessions),
            'total_minutes': total_minutes,
            'total_spent': round(total_spent, 2)
        })
    
    return jsonify(sorted(usage_data, key=lambda x: x['total_spent'], reverse=True))

# ============ PAGES ROUTES ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Ressource non trouvée'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'message': 'Erreur serveur'}), 500

# ============ DATABASE INITIALIZATION ============

def init_db():
    with app.app_context():
        db.create_all()
        
        if Tarif.query.count() == 0:
            default_tarif = Tarif(
                nom_tarif='Tarif Standard',
                prix_par_minute=0.10,
                description='Tarif par défaut - 0.10€ par minute'
            )
            db.session.add(default_tarif)
            db.session.commit()
        
        if User.query.count() == 0:
            admin = User(username='admin', email='admin@aqualand.local', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000, host='0.0.0.0')
