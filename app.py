from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import socket
import urllib.request
import time
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'map_secret_key'
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    ping_interval=10,
    ping_timeout=20,
)
port_used = 5000

# Generate a random 4-digit room password on server launch
SESSION_PASSWORD = "".join(random.choices(string.digits, k=4))

# In-memory storage for pins and visibility state
pins = []
pins_visible = True

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

@socketio.on('authenticate')
def handle_authenticate(data):
    user_pass = str(data.get('password', '')).strip()
    user_name = str(data.get('name', '')).strip()

    if user_pass == SESSION_PASSWORD and user_name:
        emit('auth_result', {'success': True, 'name': user_name})
    else:
        emit('auth_result', {'success': False, 'message': 'Incorrect password or missing name.'})

@socketio.on('connect')
def handle_connect():
    emit('load_pins', {'pins': pins, 'visible': pins_visible})
    emit('timer_update', get_current_timer_state())

@socketio.on('add_pin')
def handle_add_pin(data):
    pins.append(data)
    emit('new_pin', data, broadcast=True)

@socketio.on('toggle_pins')
def handle_toggle_pins():
    global pins_visible
    if request.remote_addr in ('127.0.0.1', '::1', local_ip):
        pins_visible = not pins_visible
        emit('pins_visibility_changed', pins_visible, broadcast=True)

@socketio.on('delete_all_pins')
def handle_delete_all_pins():
    if request.remote_addr not in ('127.0.0.1', '::1', local_ip):
        return
    pins.clear()
    emit('delete_all_pins', {'pins': pins, 'visible': pins_visible}, broadcast=True)

@socketio.on('control_timer')
def handle_control_timer(data):
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

    emit('timer_update', get_current_timer_state(), broadcast=True)

@socketio.on('delete_pin')
def handle_delete_pin(data):
    global pins
    pin_id = data.get('id')
    client_id = data.get('clientId')

    pin_to_delete = next((p for p in pins if p.get('id') == pin_id), None)

    if pin_to_delete and pin_to_delete.get('clientId') == client_id:
        pins = [p for p in pins if p.get('id') != pin_id]
        emit('pin_deleted', {'id': pin_id}, broadcast=True)

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