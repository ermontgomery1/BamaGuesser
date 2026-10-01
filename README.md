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
### PREREQUISITE INSTALLS:
- Install git: https://git-scm.com/install/windows
- Install Python: https://www.python.org/downloads/

### REPOSITORY LINK:
Repository: https://github.com/ermontgomery1/BamaGuesser.git

### GOOD COMMANDS TO KNOW IN POWERSHELL:
- Examine Files in Current Directory/Folder: ls OR dir
- Move into a directory/folder: cd DIRECTORY_NAME_HERE
- Move one directory/folder out of the current directory/folder: cd ..
- To clear the terminal: clear OR cls

### INSTRUCTIONS:
- Clone the repository: git clone https://github.com/ermontgomery1/BamaGuesser.git
- Enter the repository: cd BamaGuesser
- Setup Python Virtual Environment: ./setup.ps1
- Enter Python Virtual Environment: .\.venv\Scripts\Activate.ps1
- Start Program: python app.py
- End Program: CTRL + C
- Exit Python Virtual Environment: deactivate