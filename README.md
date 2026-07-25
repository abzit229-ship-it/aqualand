# Aqualand - Aquatic Park Management System

A local application for managing an aquatic park with RFID-based access and time-based billing.

## Features

✅ **Client Management** - Register clients with RFID badges  
✅ **Session Tracking** - Track entry/exit times and time consumed  
✅ **Billing System** - Automatic payment calculation based on time spent  
✅ **Payment History** - Record and track all payments  
✅ **Tariff Management** - Configure pricing per minute  
✅ **Active Sessions** - Real-time monitoring of current pool sessions  

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript

## Installation

1. Clone the repository:
```bash
git clone https://github.com/abzit229-ship-it/aqualand.git
cd aqualand
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## API Endpoints

### Clients
- `GET /api/clients` - List all clients
- `POST /api/clients` - Create a new client
- `GET /api/clients/<id>` - Get client details
- `PUT /api/clients/<id>` - Update client
- `DELETE /api/clients/<id>` - Delete client

### Sessions
- `GET /api/sessions` - List all sessions
- `POST /api/sessions` - Start a new session
- `POST /api/sessions/<id>/checkout` - End session and calculate payment
- `GET /api/sessions/active` - Get active sessions

## Database

The application uses SQLite with the following tables:
- **Clients** - Client information and remaining minutes
- **SessionsPiscine** - Pool session tracking
- **Paiements** - Payment history
- **Tarifs** - Pricing configuration

## License

MIT
