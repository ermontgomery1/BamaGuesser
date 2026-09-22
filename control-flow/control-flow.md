# Control Flow Charts

## Connection

### Scenario A: Manual Authentication via Modal

User Joins -> Enters Username, password, and clicks enter -> index.html:submitAuth() -> app.py:handle_connect(data) app.py:handle_authenticate(data) -> auth_result(response), load_pins(response), timer_update(response)

1. User enters name & room password -> clicks "Enter" or presses Enter key -> triggers `submitAuth()`.

2. Client executes `socket.connect()` if disconnected.

3. Client executes `socket.emit('authenticate', { name: nameVal, password: passVal })`.

4. Backend receives event -> triggers `@socketio.on('authenticate') handle_authenticate(data)`.

5. Backend verifies password against `SESSION_PASSWORD`.

6. Backend generates JWT token via `jwt.encode()` and joins socket room via `join_room(AUTH_ROOM)`.

7. Backend emits `auth_result` with token -> Client receives `socket.on('auth_result')` callback -> saves token to `sessionStorage` and hides overlay.

8. Backend emits `load_pins` event -> Client receives `socket.on('load_pins')` callback -> calls `updateLimitBtnUI()`, `addMarkerToMap()`, and `updatePinsVisibility()`.

9. Backend emits `timer_update` event -> Client receives `socket.on('timer_update')` callback -> calls `updateTimerUI()`.

### Scenario B: Reconnecting with Saved Token

1. Client page loads -> JavaScript reads `sessionStorage.getItem('jwt_token')`.

2. Client calls `socket.connect()`.

3. Backend receives Socket.IO handshake -> triggers `@socketio.on('connect') handle_connect(auth)`.

4. Backend executes `jwt.decode(token, JWT_SECRET, algorithms=["HS256"])` to validate session.

5. Backend sets session memory (`session['user_name']` & `authenticated_clients[request.sid]`).

6. Backend emits `auth_result` event -> Client receives `socket.on('auth_result')` callback to close auth modal.

7. Backend emits `load_pins` event -> Client receives `socket.on('load_pins')` callback -> calls `updateLimitBtnUI()`, `addMarkerToMap()`, and `updatePinsVisibility()`.

8. Backend emits `timer_update` event -> Client receives `socket.on('timer_update')` callback -> calls `updateTimerUI()`.

---

## User Features

### Feature: User Taps on Map (Adding a Pin)

1. User clicks/taps on map canvas -> Leaflet triggers `map.on('click', (e))` event handler.

2. Client validates `if (!isAuthenticated || !userName) return;`.

3. Client constructs `pinData` object and executes `socket.emit('add_pin', pinData)`.

4. Backend receives event -> triggers `@socketio.on('add_pin') handle_add_pin(data)`.

5. Backend verifies user socket ID in `authenticated_clients`.

6. **(If 1-Pin Limit Active)** Backend removes existing pins for user -> emits `pin_deleted` to `AUTH_ROOM` -> Clients execute `socket.on('pin_deleted')` callback to remove marker.

7. Backend appends new pin to `pins` array and executes `emit('new_pin', pin_data, to=AUTH_ROOM)`.

8. All connected clients receive event -> trigger `socket.on('new_pin', (pin))` callback.

9. Client calls `addMarkerToMap(pin)`:

* Instantiates Leaflet marker via `L.marker()`.

* Binds tooltip label via `marker.bindTooltip()`.

* Attaches marker click event listener `marker.on('click')`.

* Checks visibility condition via `isPinVisible(pin)`.

* Adds marker to rendering layer via `markersGroup.addLayer(marker)`.

---

### Feature: User Taps Own Pin (Deleting a Pin)

1. User clicks on their existing marker -> triggers `marker.on('click', (e))`.

2. Client executes `confirm("Delete your pin?")` prompt.

3. Client executes `socket.emit('delete_pin', { id: pin.id, clientId: clientId })`.

4. Backend receives event -> triggers `@socketio.on('delete_pin') handle_delete_pin(data)`.

5. Backend verifies ownership (`pin_to_delete.get('owner_sid') == request.sid`) and removes pin from list.

6. Backend executes `emit('pin_deleted', {'id': pin_id}, to=AUTH_ROOM)`.

7. All connected clients receive event -> trigger `socket.on('pin_deleted', (data))` callback.

8. Client calls `markersGroup.removeLayer(activeMarkers[data.id].marker)` and removes marker from local tracking.

---

### Feature: Host Controls & Timer

* **Toggle Pins Shown/Hidden**: Host clicks button -> `togglePins()` -> `socket.emit('toggle_pins')` -> `@socketio.on('toggle_pins') handle_toggle_pins()` -> `emit('pins_visibility_changed')` -> `socket.on('pins_visibility_changed')` -> `updatePinsVisibility()`.


* **Toggle 1-Pin Limit**: Host clicks button -> `toggleOnePinLimit()` -> `socket.emit('toggle_one_pin_limit')` -> `@socketio.on('toggle_one_pin_limit') handle_toggle_one_pin_limit()` -> `emit('one_pin_limit_changed')` -> `socket.on('one_pin_limit_changed')` -> `updateLimitBtnUI()`.


* **Delete All Pins**: Host clicks button -> `deleteAllPins()` -> `socket.emit('delete_all_pins')` -> `@socketio.on('delete_all_pins') handle_delete_all_pins()` -> `emit('delete_all_pins')` -> `socket.on('delete_all_pins')` -> `clearAllMarkers()`.


* **Timer Control (Start/Pause/Reset/Set)**: Host interacts with UI -> `toggleStartPause()` / `setTimerTime()` / `sendTimerAction()` -> `socket.emit('control_timer')` -> `@socketio.on('control_timer') handle_control_timer(data)` -> `emit('timer_update', get_current_timer_state())` -> `socket.on('timer_update')` -> `updateTimerUI()`.