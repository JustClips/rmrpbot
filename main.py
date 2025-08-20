from flask import Flask, jsonify, request
from flask_cors import CORS
import pyautogui
import time
import os

app = Flask(__name__)
CORS(app)

# Get port from environment variable  
port = int(os.environ.get('PORT', 8080))

class SimpleBot:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.current_x = self.screen_width // 2
        self.current_y = self.screen_height // 2
        
bot = SimpleBot()

@app.route('/')
def home():
    return jsonify({"message": "Bot is running!", "status": "online"})

@app.route('/status')
def status():
    # Update current position
    x, y = pyautogui.position()
    bot.current_x, bot.current_y = x, y
    
    return jsonify({
        "position": {"x": x, "y": y},
        "screen": {"width": bot.screen_width, "height": bot.screen_height}
    })

@app.route('/move/right')
def move_right():
    bot.current_x = min(bot.screen_width - 10, bot.current_x + 50)
    pyautogui.moveTo(bot.current_x, bot.current_y)
    return jsonify({"message": "Moved right", "position": {"x": bot.current_x, "y": bot.current_y}})

@app.route('/move/left')
def move_left():
    bot.current_x = max(10, bot.current_x - 50)
    pyautogui.moveTo(bot.current_x, bot.current_y)
    return jsonify({"message": "Moved left", "position": {"x": bot.current_x, "y": bot.current_y}})

@app.route('/move/to/<int:x>/<int:y>')
def move_to(x, y):
    bot.current_x = max(0, min(bot.screen_width, x))
    bot.current_y = max(0, min(bot.screen_height, y))
    pyautogui.moveTo(bot.current_x, bot.current_y)
    return jsonify({"message": f"Moved to ({bot.current_x}, {bot.current_y})"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
