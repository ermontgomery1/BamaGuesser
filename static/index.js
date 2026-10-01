//Variables BEGIN
let token = sessionStorage.getItem('jwt_token');
let userName = null;
let isAuthenticated = false;
let currentTimerState = { remaining: 300, running: false, end_time: null };
let timerInterval = null;
let onePinLimit = false;
let globalPinsVisible = true;
const socket = io({
    auth: { token: token },
    autoConnect: false
});
const clientId = localStorage.getItem('user_client_id') || 'user_' + Math.random().toString(36).substring(2, 11);
localStorage.setItem('user_client_id', clientId);
const campusBounds = L.latLngBounds(
    [33.1800, -87.5870], // Southwest coordinate
    [33.2400, -87.4870]  // Northeast coordinate
);
const map = L.map('map', {
    tap: true,
    maxBounds: campusBounds,
    maxBoundsViscosity: 0.6,       // Set between 0.5 and 0.8 to make edges feel softer/elastic
    minZoom: 13,                  // Lowered to 13 to allow viewing the larger boundary
    maxZoom: 19
}).fitBounds([
    [33.1950, -87.5620],           // Keeps default view focused tightly on core campus
    [33.2250, -87.5120]
]);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    minZoom: 13,
    maxZoom: 19,
    bounds: campusBounds,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);
const markersGroup = L.layerGroup().addTo(map);
const activeMarkers = {};
//Variables END

function submitAuth() {
    const nameVal = document.getElementById('user-name-input').value.trim();
    const passVal = document.getElementById('user-pass-input').value.trim();
    const errDiv = document.getElementById('auth-error');

    //If the new user does not provide both a name and a password
    if (!nameVal || !passVal) {
        errDiv.innerText = "Please provide both a name and password.";
        errDiv.style.display = "block";
        return;
    }

    if (!socket.connected) {
        socket.connect();
    }

    //Hand off information to backend
    socket.emit('authenticate', { name: nameVal, password: passVal });
}

socket.on('auth_result', (response) => {
    const errDiv = document.getElementById('auth-error');
    if (response.success) {
        userName = response.name;
        isAuthenticated = true;

        if (response.token) {
            sessionStorage.setItem('jwt_token', response.token); //Saves the unique token to the users browser
            socket.auth = { token: response.token }; //Updates the authentication credentials stored on the Socket.IO client so they are sent during future connection attempts (reconnections).
        }

        //Hide the login screen
        document.getElementById('auth-overlay').style.display = 'none';
    } else {
        errDiv.innerText = response.message || "Authentication failed.";
        errDiv.style.display = "block";
    }
});

socket.on('connect_error', (err) => {
    // 1. Reset state & remove invalid token
    sessionStorage.removeItem('jwt_token');
    socket.auth = {};
    isAuthenticated = false;
    userName = null;

    // 2. Re-display the login modal
    const authOverlay = document.getElementById('auth-overlay');
    const errDiv = document.getElementById('auth-error');

    if (authOverlay) {
        // Setting to empty string restores the display mode defined in index.css (e.g. flex)
        authOverlay.style.display = ''; 
    }

    // 3. Show error message to user
    if (errDiv) {
        errDiv.innerText = "Session expired or invalid login. Please re-enter credentials.";
        errDiv.style.display = "block";
    }
});

function updateLimitBtnUI(enabled) {
    onePinLimit = enabled;
    const limitBtn = document.getElementById('limit-btn');
    if (limitBtn) {
        limitBtn.innerText = enabled ? "1 Pin Limit: ON" : "1 Pin Limit: OFF";
    }
}

function addMarkerToMap(pin) {
    if (activeMarkers[pin.id]) return;

    const marker = L.marker([pin.lat, pin.lng]);
    
    if (pin.label) {
        marker.bindTooltip(`<b>${pin.label}</b>`, {
            permanent: true,
            direction: 'top',
            offset: [0, -10],
            className: 'pin-label'
        });
    }

    if (pin.clientId === clientId) {
        marker.on('click', (e) => {
            L.DomEvent.stopPropagation(e);
            if (confirm(`Delete your pin?`)) {
                socket.emit('delete_pin', { id: pin.id, clientId: clientId });
            }
        });
    }

    activeMarkers[pin.id] = { marker: marker, pin: pin };

    if (isPinVisible(pin)) {
        markersGroup.addLayer(marker);
    }
}

function isPinVisible(pin) {
    return globalPinsVisible || pin.clientId === clientId;
}

function updatePinsVisibility(isVisible) {
    globalPinsVisible = isVisible;

    for (let id in activeMarkers) {
        const item = activeMarkers[id];
        if (isPinVisible(item.pin)) {
            if (!markersGroup.hasLayer(item.marker)) {
                markersGroup.addLayer(item.marker);
            }
        } else {
            if (markersGroup.hasLayer(item.marker)) {
                markersGroup.removeLayer(item.marker);
            }
        }
    }

    const toggleBtn = document.getElementById('toggle-btn');
    if (toggleBtn) {
        toggleBtn.innerText = globalPinsVisible ? "Pins: SHOWN" : "Pins: HIDDEN";
    }
}

socket.on('load_pins', (data) => {
    if (data.one_pin_limit !== undefined) {
        updateLimitBtnUI(data.one_pin_limit);
    }
    if (data.lock_pins !== undefined) {
        updateLockPinsUI(data.lock_pins);
    }
    data.pins.forEach(addMarkerToMap);
    updatePinsVisibility(data.visible);
});

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function updateTimerUI() {
    let displaySecs = currentTimerState.remaining;

    if (currentTimerState.running && currentTimerState.end_time) {
        const now = Date.now() / 1000;
        displaySecs = Math.max(0, Math.ceil(currentTimerState.end_time - now));
    }

    document.getElementById('timer-display').innerText = formatTime(displaySecs);

    const startBtn = document.getElementById('timer-start-btn');
    if (startBtn) {
        startBtn.innerText = currentTimerState.running ? "Pause" : "Start";
    }
}

socket.on('timer_update', (state) => {
    currentTimerState = state;
    updateTimerUI();

    if (timerInterval) clearInterval(timerInterval);
    if (currentTimerState.running) {
        timerInterval = setInterval(updateTimerUI, 200);
    }
});

// Automatically connect AFTER registering listeners
if (token) {
    socket.connect();
}

function sendTimerAction(action, minutes = null, seconds = null) {
    socket.emit('control_timer', { action: action, minutes: minutes, seconds: seconds });
}

function setTimerTime() {
    const mins = parseInt(document.getElementById('timer-min-input').value, 10) || 0;
    const secs = parseInt(document.getElementById('timer-sec-input').value, 10) || 0;
    
    if (mins >= 0 && secs >= 0 && (mins > 0 || secs > 0)) {
        sendTimerAction('set', mins, secs);
    }
}

function toggleStartPause() {
    if (currentTimerState.running) {
        sendTimerAction('pause');
    } else {
        sendTimerAction('start');
    }
}

// --- PIN SOCKET EVENT HANDLERS ---
function clearAllMarkers() {
    markersGroup.clearLayers();
    for (let id in activeMarkers) {
        delete activeMarkers[id];
    }
}

socket.on('delete_all_pins', (data) => {
    clearAllMarkers();
    data.pins.forEach(addMarkerToMap);
    updatePinsVisibility(data.visible);
});

socket.on('one_pin_limit_changed', (enabled) => {
    updateLimitBtnUI(enabled);
});

function toggleOnePinLimit() {
    socket.emit('toggle_one_pin_limit');
}

socket.on('new_pin', (pin) => {
    addMarkerToMap(pin);
});

socket.on('pins_visibility_changed', (isVisible) => {
    updatePinsVisibility(isVisible);
});

map.on('click', (e) => {
    if (!isAuthenticated || !userName) return;

    const pinData = {
        id: Date.now() + '-' + Math.random().toString(36).substring(2, 9),
        lat: e.latlng.lat,
        lng: e.latlng.lng,
        clientId: clientId
    };

    socket.emit('add_pin', pinData);
});

function togglePins() {
    socket.emit('toggle_pins');
}

function toggleLockPins() {
    socket.emit('toggle_lock_pins');
}

function deleteAllPins() {
    socket.emit('delete_all_pins');
}

function updateLockPinsUI(isLocked) {
    const toggleLockBtn = document.getElementById('toggle-lock-pins-txt');
    if (toggleLockBtn) {
        toggleLockBtn.innerText = isLocked ? "Pins: LOCKED" : "Pins: UNLOCKED";
    }
}

socket.on('toggle_lock_pins', (data) =>{
    updateLockPinsUI(data.lock_pins);
});

socket.on('pin_deleted', (data) => {
    if (activeMarkers[data.id]) {
        markersGroup.removeLayer(activeMarkers[data.id].marker);
        delete activeMarkers[data.id];
    }
});