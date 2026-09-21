from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, disconnect
import socket
import urllib.request
import time
import string
import secrets
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'map_secret_key'
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    ping_interval=10,
    ping_timeout=20,
)
port_used = 5000
AUTH_ROOM = 'authenticated'

# Generate a token and password on server launch
JWT_SECRET = secrets.token_hex(32)
SESSION_PASSWORD = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))

# Track authenticated socket IDs and user names in server memory
authenticated_clients = {}  # { request.sid: user_name }

# In-memory storage for pins and visibility state
pins = []
pins_visible = True
one_pin_limit = False  # New global setting for 1-pin limit

# Timer state
timer_data = {
    'duration': 300,   # Default set duration (5 mins in seconds)
    'remaining': 300,  # Remaining time in seconds when paused
    'running': False,
    'end_time': None   # Unix timestamp when timer ends
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

local_ip = get_local_ip()

def get_current_timer_state():
    if timer_data['running'] and timer_data['end_time']:
        rem = max(0, int(timer_data['end_time'] - time.time()))
        return {
            'remaining': rem,
            'running': rem > 0,
            'end_time': timer_data['end_time']
        }
    return {
        'remaining': timer_data['remaining'],
        'running': False,
        'end_time': None
    }

@app.route('/')
def index():
    is_host = request.remote_addr in ('127.0.0.1', '::1', local_ip)
    return render_template('index.html', is_host=is_host)

@socketio.on('connect')
def handle_connect(auth=None):
    # Safely retrieve token sent during Socket.IO handshake
    token = auth.get('token') if isinstance(auth, dict) else None
    
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_name = payload.get('user_name')
            if user_name:
                session['user_name'] = user_name
                authenticated_clients[request.sid] = user_name
                
                # Notify client that existing token was accepted
                emit('auth_result', {'success': True, 'token': token, 'name': user_name})
                emit('load_pins', {
                    'pins': pins, 
                    'visible': pins_visible, 
                    'one_pin_limit': one_pin_limit
                })
                emit('timer_update', get_current_timer_state())
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass

@socketio.on('disconnect')
def handle_disconnect():
    authenticated_clients.pop(request.sid, None)

@socketio.on('authenticate')
def handle_authenticate(data):
    password = data.get('password')
    name = data.get('name')

    if password == SESSION_PASSWORD and name:
        authenticated_clients[request.sid] = name

        token = jwt.encode({
            'user_name': name,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        }, JWT_SECRET, algorithm="HS256")

        emit('auth_result', {'success': True, 'token': token, 'name': name})
        emit('load_pins', {
            'pins': pins, 
            'visible': pins_visible, 
            'one_pin_limit': one_pin_limit
        })
        emit('timer_update', get_current_timer_state())
    else:
        emit('auth_result', {'success': False, 'message': 'Invalid room password or name.'})

@socketio.on('add_pin')
def handle_add_pin(data):
    if request.sid not in authenticated_clients:
        return
    
    global pins
    client_id = data.get('clientId')
    user_name = authenticated_clients[request.sid]

    # If 1-pin limit is enabled, remove user's existing pins first
    if one_pin_limit:
        existing_pins = [
            p for p in pins 
            if p.get('clientId') == client_id or p.get('owner_sid') == request.sid
        ]
        for old_pin in existing_pins:
            pins.remove(old_pin)
            emit('pin_deleted', {'id': old_pin['id']}, to=AUTH_ROOM)

    pin_data = {
        'id': data.get('id'),
        'lat': data.get('lat'),
        'lng': data.get('lng'),
        'label': user_name,
        'clientId': client_id,
        'owner_sid': request.sid
    }
    pins.append(pin_data)
    emit('new_pin', pin_data, to=AUTH_ROOM)


@socketio.on('toggle_one_pin_limit')
def handle_toggle_one_pin_limit():
    if request.sid not in authenticated_clients:
        return
    if request.remote_addr not in ('127.0.0.1', '::1', local_ip):
        return
    
    global one_pin_limit
    one_pin_limit = not one_pin_limit
    emit('one_pin_limit_changed', one_pin_limit, to=AUTH_ROOM)

@socketio.on('delete_pin')
def handle_delete_pin(data):
    if request.sid not in authenticated_clients:
        return
    
    global pins
    pin_id = data.get('id')
    pin_to_delete = next((p for p in pins if p.get('id') == pin_id), None)

    if pin_to_delete and pin_to_delete.get('owner_sid') == request.sid:
        pins = [p for p in pins if p.get('id') != pin_id]
        emit('pin_deleted', {'id': pin_id}, to=AUTH_ROOM)

@socketio.on('toggle_pins')
def handle_toggle_pins():
    if request.sid not in authenticated_clients:
        return
    global pins_visible
    if request.remote_addr in ('127.0.0.1', '::1', local_ip):
        pins_visible = not pins_visible
        emit('pins_visibility_changed', pins_visible, to=AUTH_ROOM)

@socketio.on('delete_all_pins')
def handle_delete_all_pins():
    if request.sid not in authenticated_clients:
        return
    if request.remote_addr not in ('127.0.0.1', '::1', local_ip):
        return
    pins.clear()
    emit('delete_all_pins', {'pins': pins, 'visible': pins_visible}, to=AUTH_ROOM)

@socketio.on('control_timer')
def handle_control_timer(data):
    if request.sid not in authenticated_clients:
        return
    if request.remote_addr not in ('127.0.0.1', '::1', local_ip):
        return

    action = data.get('action')
    current_time = time.time()

    if action == 'start':
        if not timer_data['running'] and timer_data['remaining'] > 0:
            timer_data['running'] = True
            timer_data['end_time'] = current_time + timer_data['remaining']
    elif action == 'pause':
        if timer_data['running'] and timer_data['end_time']:
            timer_data['remaining'] = max(0, int(timer_data['end_time'] - current_time))
            timer_data['running'] = False
            timer_data['end_time'] = None
    elif action == 'reset':
        timer_data['running'] = False
        timer_data['remaining'] = timer_data['duration']
        timer_data['end_time'] = None
    elif action == 'set':
        minutes = data.get('minutes', 0)
        seconds = data.get('seconds', 0)
        try:
            total_seconds = (int(minutes) * 60) + int(seconds)
            if total_seconds > 0:
                timer_data['duration'] = total_seconds
                timer_data['remaining'] = total_seconds
                timer_data['running'] = False
                timer_data['end_time'] = None
        except (ValueError, TypeError):
            pass

    emit('timer_update', get_current_timer_state(), to=AUTH_ROOM)

def print_link():
    try:
        public_ip = urllib.request.urlopen("https://api.ipify.org", timeout=3).read().decode("utf-8")
    except Exception:
        public_ip = "Unavailable / Offline"

    print("=" * 40)
    print(f" SESSION PASSWORD:  {SESSION_PASSWORD}")
    print("=" * 40)
    print(f" Local IP (LAN):    {local_ip}")
    print(f" Public IP (WAN):   {public_ip}")
    print(f" Access Map at:     http://{local_ip}:{port_used}")
    print("=" * 40)

if __name__ == '__main__':
    print_link()
    socketio.run(app, host='0.0.0.0', port=port_used)