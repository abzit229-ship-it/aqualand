// API Base URL
const API_BASE = '/api';
let currentTarif = 0.10; // Default tariff

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    updateTime();
    setInterval(updateTime, 1000);
    loadDashboard();
    setInterval(loadDashboard, 5000); // Refresh every 5 seconds
});

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString('fr-FR');
}

// Tab Management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all nav links
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName).classList.add('active');

    // Add active class to clicked link
    event.target.classList.add('active');

    // Update page title
    const titles = {
        'dashboard': '📊 Tableau de Bord',
        'clients': '👥 Clients',
        'sessions': '🕐 Sessions',
        'tarifs': '💰 Tarifs',
        'paiements': '💳 Paiements'
    };
    document.getElementById('page-title').textContent = titles[tabName];

    // Load data for the tab
    if (tabName === 'clients') loadClients();
    if (tabName === 'sessions') loadSessions();
    if (tabName === 'tarifs') loadTarifs();
    if (tabName === 'paiements') loadPaiements();
}

// ============ DASHBOARD ============

async function loadDashboard() {
    try {
        const [clients, sessions, paiements] = await Promise.all([
            fetch(`${API_BASE}/clients`).then(r => r.json()),
            fetch(`${API_BASE}/sessions`).then(r => r.json()),
            fetch(`${API_BASE}/paiements`).then(r => r.json()).catch(() => [])
        ]);

        // Count active sessions
        const activeSessions = sessions.filter(s => s.statut === 'EN_COURS');
        document.getElementById('active-clients').textContent = clients.length;
        document.getElementById('active-sessions').textContent = activeSessions.length;

        // Calculate revenue
        const today = new Date().toDateString();
        const todayRevenue = sessions
            .filter(s => new Date(s.heure_entree).toDateString() === today)
            .reduce((sum, s) => sum + s.montant_paye, 0);
        document.getElementById('daily-revenue').textContent = todayRevenue.toFixed(2) + '€';

        // Calculate total minutes
        const totalMinutes = sessions.reduce((sum, s) => sum + (s.minutes_consommees || 0), 0);
        document.getElementById('total-minutes').textContent = totalMinutes;

        // Load active sessions table
        loadActiveSessionsTable(activeSessions);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function loadActiveSessionsTable(sessions) {
    const tbody = document.querySelector('#active-sessions-table tbody');
    tbody.innerHTML = '';

    if (sessions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#999;">Aucune session active</td></tr>';
        return;
    }

    sessions.forEach(session => {
        const entree = new Date(session.heure_entree);
        const now = new Date();
        const duration = Math.floor((now - entree) / 60000); // minutes

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${session.badge_rfid}</td>
            <td>${entree.toLocaleString('fr-FR')}</td>
            <td>${duration} min</td>
            <td>
                <button class="btn btn-success btn-small" onclick="openCheckoutModal(${session.id_session})">
                    Clôturer
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// ============ CLIENTS ============

function showClientForm() {
    document.getElementById('client-form').style.display = 'block';
}

function closeClientForm() {
    document.getElementById('client-form').style.display = 'none';
    document.getElementById('client-nom').value = '';
    document.getElementById('client-rfid').value = '';
    document.getElementById('client-minutes').value = '0';
}

async function saveClient(event) {
    event.preventDefault();

    const clientData = {
        nom: document.getElementById('client-nom').value,
        badge_rfid: document.getElementById('client-rfid').value,
        minutes_restantes: parseInt(document.getElementById('client-minutes').value)
    };

    try {
        const response = await fetch(`${API_BASE}/clients`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData)
        });

        if (response.ok) {
            showNotification('Client ajouté avec succès!', 'success');
            closeClientForm();
            loadClients();
        } else {
            showNotification('Erreur lors de l\'ajout du client', 'danger');
        }
    } catch (error) {
        console.error('Error saving client:', error);
        showNotification('Erreur: ' + error.message, 'danger');
    }
}

async function loadClients() {
    try {
        const clients = await fetch(`${API_BASE}/clients`).then(r => r.json());
        const tbody = document.querySelector('#clients-table tbody');
        tbody.innerHTML = '';

        clients.forEach(client => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${client.id_client}</td>
                <td>${client.nom}</td>
                <td>${client.badge_rfid}</td>
                <td>${client.minutes_restantes}</td>
                <td>
                    <button class="btn btn-danger btn-small" onclick="deleteClient(${client.id_client})">
                        Supprimer
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading clients:', error);
    }
}

async function deleteClient(clientId) {
    if (!confirm('Êtes-vous sûr?')) return;

    try {
        await fetch(`${API_BASE}/clients/${clientId}`, { method: 'DELETE' });
        showNotification('Client supprimé!', 'success');
        loadClients();
    } catch (error) {
        console.error('Error deleting client:', error);
        showNotification('Erreur lors de la suppression', 'danger');
    }
}

// ============ SESSIONS ============

function showSessionForm() {
    document.getElementById('session-form').style.display = 'block';
}

function closeSessionForm() {
    document.getElementById('session-form').style.display = 'none';
    document.getElementById('session-rfid').value = '';
}

async function startSession(event) {
    event.preventDefault();

    const sessionData = {
        badge_rfid: document.getElementById('session-rfid').value
    };

    try {
        const response = await fetch(`${API_BASE}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sessionData)
        });

        if (response.ok) {
            showNotification('Session démarrée!', 'success');
            closeSessionForm();
            loadSessions();
            loadDashboard();
        } else {
            showNotification('Erreur lors du démarrage de la session', 'danger');
        }
    } catch (error) {
        console.error('Error starting session:', error);
        showNotification('Erreur: ' + error.message, 'danger');
    }
}

async function loadSessions() {
    try {
        const sessions = await fetch(`${API_BASE}/sessions`).then(r => r.json());
        const tbody = document.querySelector('#sessions-table tbody');
        tbody.innerHTML = '';

        sessions.forEach(session => {
            const entree = new Date(session.heure_entree);
            const sortie = session.heure_sortie ? new Date(session.heure_sortie) : null;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${session.id_session}</td>
                <td>${session.badge_rfid}</td>
                <td>${entree.toLocaleString('fr-FR')}</td>
                <td>${sortie ? sortie.toLocaleString('fr-FR') : '-'}</td>
                <td>${session.minutes_consommees || '-'}</td>
                <td>${session.montant_paye.toFixed(2)}€</td>
                <td>
                    <span class="badge ${session.statut === 'EN_COURS' ? 'badge-success' : 'badge-danger'}">
                        ${session.statut}
                    </span>
                </td>
                <td>
                    ${session.statut === 'EN_COURS' ? `
                        <button class="btn btn-success btn-small" onclick="openCheckoutModal(${session.id_session})">
                            Clôturer
                        </button>
                    ` : '-'}
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

function openCheckoutModal(sessionId) {
    document.getElementById('checkout-session-id').value = sessionId;
    document.getElementById('checkout-modal').style.display = 'block';
}

function closeCheckoutModal() {
    document.getElementById('checkout-modal').style.display = 'none';
}

async function checkoutSession(event) {
    event.preventDefault();

    const sessionId = document.getElementById('checkout-session-id').value;
    const tarif = parseFloat(document.getElementById('checkout-tarif').value);

    try {
        const response = await fetch(`${API_BASE}/sessions/${sessionId}/checkout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prix_par_minute: tarif })
        });

        if (response.ok) {
            const data = await response.json();
            showNotification(`Session clôturée! Montant: ${data.montant_paye}€`, 'success');
            closeCheckoutModal();
            loadSessions();
            loadDashboard();
        } else {
            showNotification('Erreur lors de la clôture', 'danger');
        }
    } catch (error) {
        console.error('Error checking out:', error);
        showNotification('Erreur: ' + error.message, 'danger');
    }
}

// ============ TARIFS ============

function showTarifForm() {
    document.getElementById('tarif-form').style.display = 'block';
}

function closeTarifForm() {
    document.getElementById('tarif-form').style.display = 'none';
    document.getElementById('tarif-nom').value = '';
    document.getElementById('tarif-prix').value = '';
    document.getElementById('tarif-description').value = '';
}

async function saveTarif(event) {
    event.preventDefault();

    const tarifData = {
        nom_tarif: document.getElementById('tarif-nom').value,
        prix_par_minute: parseFloat(document.getElementById('tarif-prix').value),
        description: document.getElementById('tarif-description').value
    };

    try {
        const response = await fetch(`${API_BASE}/tarifs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tarifData)
        });

        if (response.ok) {
            showNotification('Tarif ajouté!', 'success');
            closeTarifForm();
            loadTarifs();
        } else {
            showNotification('Erreur lors de l\'ajout du tarif', 'danger');
        }
    } catch (error) {
        console.error('Error saving tarif:', error);
        showNotification('Erreur: ' + error.message, 'danger');
    }
}

async function loadTarifs() {
    try {
        const tarifs = await fetch(`${API_BASE}/tarifs`).then(r => r.json()).catch(() => []);
        const tbody = document.querySelector('#tarifs-table tbody');
        tbody.innerHTML = '';

        if (tarifs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#999;">Aucun tarif</td></tr>';
            return;
        }

        tarifs.forEach(tarif => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${tarif.id_tarif}</td>
                <td>${tarif.nom_tarif}</td>
                <td>${tarif.prix_par_minute.toFixed(2)}€/min</td>
                <td>${tarif.description || '-'}</td>
                <td>
                    <button class="btn btn-danger btn-small" onclick="deleteTarif(${tarif.id_tarif})">
                        Supprimer
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading tarifs:', error);
    }
}

async function deleteTarif(tarifId) {
    if (!confirm('Êtes-vous sûr?')) return;

    try {
        await fetch(`${API_BASE}/tarifs/${tarifId}`, { method: 'DELETE' });
        showNotification('Tarif supprimé!', 'success');
        loadTarifs();
    } catch (error) {
        console.error('Error deleting tarif:', error);
        showNotification('Erreur lors de la suppression', 'danger');
    }
}

// ============ PAIEMENTS ============

async function loadPaiements() {
    try {
        const paiements = await fetch(`${API_BASE}/paiements`).then(r => r.json()).catch(() => []);
        const tbody = document.querySelector('#paiements-table tbody');
        tbody.innerHTML = '';

        if (paiements.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#999;">Aucun paiement</td></tr>';
            return;
        }

        paiements.forEach(paiement => {
            const date = new Date(paiement.date_paiement);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${paiement.id_paiement}</td>
                <td>${paiement.id_client}</td>
                <td>${paiement.montant.toFixed(2)}€</td>
                <td>${date.toLocaleString('fr-FR')}</td>
                <td>${paiement.type_paiement || '-'}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading paiements:', error);
    }
}

// ============ UTILITIES ============

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${type === 'success' ? '#28a745' : type === 'danger' ? '#dc3545' : '#17a2b8'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Close modals when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('checkout-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Initialize with dashboard tab
document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('.nav-menu a').classList.add('active');
});
