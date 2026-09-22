# BamaGuesser

## Introduction

BamaGuesser is an interactive map made for real-time pin sharing between users built using Python (Flask-SocketIO) and JavaScript (Leaflet.js & Socket.IO).

## Features

* **Real-Time Interactive Pinning:** Click anywhere on the map to drop a pin tagged with your display name. Pins update instantly for all connected users via WebSockets.
* **Session Authentication:** Generates a random 4-digit passcode on server startup. Users must enter their display name and room passcode to gain access.
* **Role-Based Host Controls:** Automatically identifies host connections (running from local machine/host IP).
* **Synchronized Shared Timer:** A global countdown timer visible to all participants. Host user can set, start, pause, and reset time, keeping all connected clients in sync.

## Tech Stack

* **Backend:** Python 3, Flask, Flask-SocketIO
* **Frontend:** HTML5, CSS3, JavaScript (ES6)
* **Mapping Library:** Leaflet.js with OpenStreetMap tile layer
* **Real-Time Protocol:** WebSockets Socket.IO

## Project Structure

```text
.
├── app.py                # Flask server, WebSocket event handlers, timer & auth state
├── static/
│   └── index.css         # Styling for host controls, timer widget, and map tooltips
└── templates/
    └── index.html        # Main template, Leaflet map setup, and client Socket.IO logic
```

## Installation & Setup

### Prerequisites

* Python 3.8 or higher
* `pip` (Python package installer)

### Step 1: Clone or Copy the Repository

Ensure files are organized according to Flask's standard directory structure:

```bash
mkdir -p static templates
# Move index.css to static/
# Move index.html to templates/
```

### Step 2: Install Dependencies

Install the required Python packages:

```bash
pip install flask flask-socketio
```

*Note: Depending on your deployment environment, you may also want to install an asynchronous server library such as `gevent-websocket` or `eventlet`.*

```bash
pip install gevent-websocket

```