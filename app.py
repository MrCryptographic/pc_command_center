# FILE: app.py

from flask import Flask, render_template, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import psutil
import os
import pyautogui
import pyperclip  # For clipboard access
from plyer import notification  # For desktop notifications
import io # For sending images without saving to disk

# --- CONFIGURATION ---
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
TODO_FILE = 'todo.txt'

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__, template_folder='templates')
CORS(app)

# Ensure required folders exist
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- HELPER FUNCTIONS ---
def get_todo_items():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, 'r') as f:
        return [line.strip() for line in f.readlines()]

def save_todo_items(items):
    with open(TODO_FILE, 'w') as f:
        for item in items:
            f.write(f"{item}\n")

# --- HTML SERVING ROUTE ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API ROUTES ---

@app.route('/api/processes')
def get_processes():
    """Returns top 5 processes by CPU usage."""
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent']):
        procs.append(proc.info)
    top_procs = sorted(procs, key=lambda p: p['cpu_percent'], reverse=True)[:5]
    return jsonify(top_procs)

@app.route('/api/clipboard', methods=['GET', 'POST'])
def handle_clipboard():
    """Handles getting and setting the PC's clipboard."""
    if request.method == 'GET':
        return jsonify({'clipboard_content': pyperclip.paste()})
    elif request.method == 'POST':
        content = request.json.get('content', '')
        pyperclip.copy(content)
        return jsonify({'status': 'success', 'message': 'PC clipboard set.'})

@app.route('/api/type_string', methods=['POST'])
def type_string():
    """Types a given string on the PC."""
    text_to_type = request.json.get('text', '')
    pyautogui.typewrite(text_to_type, interval=0.01)
    return jsonify({'status': 'success', 'message': 'Text typed.'})

@app.route('/api/notify', methods=['POST'])
def send_notification():
    """Sends a desktop notification to the PC."""
    title = request.json.get('title', 'Notification from Phone')
    message = request.json.get('message', 'No message content.')
    try:
        notification.notify(title=title, message=message, app_name='PC Dashboard', timeout=10)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/screenshot')
def get_screenshot():
    """Takes a screenshot and returns it as an image response."""
    screenshot = pyautogui.screenshot()
    img_io = io.BytesIO()
    screenshot.save(img_io, 'PNG')
    img_io.seek(0)
    return Response(img_io, mimetype='image/png')
    
@app.route('/api/control', methods=['POST'])
def system_control():
    """Handles PC, media, macros, and custom commands."""
    action_type = request.json.get('type', 'command')
    
    if action_type == 'command':
        command = request.json.get('command')
        if not command: return jsonify({'status': 'error', 'message': 'No command provided'}), 400
        print(f"Received command: {command}")
        
        if command == 'shutdown': os.system('shutdown /s /t 1')
        elif command == 'restart': os.system('shutdown /r /t 1')
        elif command == 'sleep': os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        elif command in ['playpause', 'nexttrack', 'prevtrack', 'volumeup', 'volumedown']: pyautogui.press(command)
        elif command == 'shortcut_copy': pyautogui.hotkey('ctrl', 'c')
        else: return jsonify({'status': 'error', 'message': 'Unknown command'}), 400
        return jsonify({'status': 'success', 'command': command})

    elif action_type == 'custom':
        custom_command = request.json.get('command')
        if not custom_command: return jsonify({'status': 'error', 'message': 'No custom command provided'}), 400
        print(f"Executing custom command: {custom_command}")
        os.system(custom_command)
        return jsonify({'status': 'success', 'message': f"Executed: {custom_command}"})

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'cpu': psutil.cpu_percent(interval=0.1),
        'ram': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent
    })

# NOTE: The To-Do and File Manager routes from v1 are excluded here for brevity,
# but can be added back in from the previous response if you still want them.

# --- RUN THE APP ---
if __name__ == '__main__':
    print("--- PC Command Center v2.0 ---")
    print("Access this dashboard from another device on the same network using:")
    print("http://YOUR_PC_IP_ADDRESS:5000")
    print("------------------------------")
    app.run(host='0.0.0.0', port=5000, debug=False)