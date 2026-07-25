-- Table des clients possédant un pass horaire rechargeable
CREATE TABLE Clients (
    id_client INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    badge_rfid TEXT UNIQUE,
    minutes_restantes INTEGER DEFAULT 0
);

-- Table des sessions en cours (entrées/sorties)
CREATE TABLE SessionsPiscine (
    id_session INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_rfid TEXT NOT NULL,
    heure_entree DATETIME NOT NULL,
    heure_sortie DATETIME,
    minutes_consommees INTEGER,
    montant_paye REAL DEFAULT 0.0,
    statut TEXT CHECK(statut IN ('EN_COURS', 'TERMINE')) DEFAULT 'EN_COURS'
);

-- Table de l'historique des paiements
CREATE TABLE Paiements (
    id_paiement INTEGER PRIMARY KEY AUTOINCREMENT,
    id_client INTEGER NOT NULL,
    montant REAL NOT NULL,
    date_paiement DATETIME DEFAULT CURRENT_TIMESTAMP,
    type_paiement TEXT CHECK(type_paiement IN ('CASH', 'CARTE', 'CHEQUE')),
    FOREIGN KEY (id_client) REFERENCES Clients(id_client)
);

-- Table de tarification
CREATE TABLE Tarifs (
    id_tarif INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_tarif TEXT NOT NULL,
    prix_par_minute REAL NOT NULL,
    description TEXT
);
