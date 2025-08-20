from flask import Flask, jsonify
from flask_cors import CORS
import pyautogui
import os

app = Flask(__name__)
CORS(app)

# Get port from environment variable or default to 8080
port = int(os.environ.get('PORT', 8080))

@app.route('/')
def home():
    return jsonify({
        "message": "Color Bot Backend Running",
        "status": "online"
    })

@app.route('/status')
def status():
    try:
        screen_width, screen_height = pyautogui.size()
        current_x, current_y = pyautogui.position()
        return jsonify({
            "current_position": {"x": current_x, "y": current_y},
            "screen_size": {"width": screen_width, "height": screen_height}
        })
    except:
        return jsonify({
            "current_position": {"x": 0, "y": 0},
            "screen_size": {"width": 0, "height": 0},
            "error": "Cannot access screen"
        })

@app.route('/test-move', methods=['POST'])
def test_move():
    try:
        screen_width, screen_height = pyautogui.size()
        pyautogui.moveTo(screen_width // 2, screen_height // 2)
        return jsonify({"message": "Moved to center"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
