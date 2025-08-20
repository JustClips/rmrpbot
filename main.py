from flask import Flask, jsonify, request
from flask_cors import CORS
import pyautogui
import cv2
import numpy as np
import time
import threading
import os
from collections import deque

app = Flask(__name__)
CORS(app)

# Get port from environment variable or default to 8080
port = int(os.environ.get('PORT', 8080))

class EnhancedColorBot:
    def __init__(self):
        # Screen setup
        self.screen_width, self.screen_height = pyautogui.size()
        self.current_x = self.screen_width // 2
        self.current_y = self.screen_height // 2
        
        # Bot state
        self.is_running = False
        self.is_scanning = False
        self.target_found = False
        self.scan_results = []
        
        # Performance settings
        self.scan_step = 10  # Smaller steps for accuracy
        self.scan_range = 300  # Wider search area
        self.green_threshold = 0.15  # Lower threshold for sensitivity
        self.smooth_movement = True
        
        # Tracking
        self.movement_history = deque(maxlen=10)
        self.best_positions = []
        
    def detect_green_precise(self, region):
        """High-precision green detection"""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot(region=region)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Multiple green ranges for better detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Range 1: Standard green
            lower_green1 = np.array([35, 50, 50])
            upper_green1 = np.array([85, 255, 255])
            mask1 = cv2.inRange(hsv, lower_green1, upper_green1)
            
            # Range 2: Bright green
            lower_green2 = np.array([40, 100, 100])
            upper_green2 = np.array([70, 255, 255])
            mask2 = cv2.inRange(hsv, lower_green2, upper_green2)
            
            # Combine masks
            mask = cv2.bitwise_or(mask1, mask2)
            
            # Clean up noise
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            green_pixels = cv2.countNonZero(mask)
            total_pixels = mask.shape[0] * mask.shape[1]
            
            green_ratio = green_pixels / total_pixels if total_pixels > 0 else 0
            
            # Calculate center of green mass for more precise targeting
            if green_pixels > 0:
                moments = cv2.moments(mask)
                if moments["m00"] != 0:
                    cx = int(moments["m10"] / moments["m00"])
                    cy = int(moments["m01"] / moments["m00"])
                    return {
                        "ratio": float(green_ratio),
                        "center_offset_x": cx - 25,  # 25 is half of 50px region
                        "center_offset_y": cy - 25
                    }
            
            return {"ratio": float(green_ratio), "center_offset_x": 0, "center_offset_y": 0}
            
        except Exception as e:
            return {"ratio": 0.0, "center_offset_x": 0, "center_offset_y": 0, "error": str(e)}
    
    def smooth_move_to(self, target_x, target_y, steps=5):
        """Smooth cursor movement"""
        if not self.smooth_movement:
            pyautogui.moveTo(target_x, target_y)
            return
            
        current_x, current_y = pyautogui.position()
        delta_x = (target_x - current_x) / steps
        delta_y = (target_y - current_y) / steps
        
        for i in range(steps):
            new_x = current_x + delta_x * (i + 1)
            new_y = current_y + delta_y * (i + 1)
            pyautogui.moveTo(int(new_x), int(new_y))
            time.sleep(0.02)  # 20ms between moves
    
    def continuous_scan(self):
        """24/7 scanning in background"""
        self.is_scanning = True
        self.scan_results = []
        
        while self.is_scanning:
            try:
                # Scan wider area with smaller steps
                best_ratio = 0
                best_x = self.current_x
                best_y = self.current_y
                results = []
                
                for offset_x in range(-self.scan_range, self.scan_range + 1, self.scan_step):
                    for offset_y in range(-self.scan_range//2, self.scan_range//2 + 1, self.scan_step):
                        x_pos = max(25, min(self.screen_width - 25, self.current_x + offset_x))
                        y_pos = max(25, min(self.screen_height - 25, self.current_y + offset_y))
                        
                        region = (int(x_pos - 25), int(y_pos - 25), 50, 50)
                        result = self.detect_green_precise(region)
                        
                        results.append({
                            "x": int(x_pos),
                            "y": int(y_pos),
                            "ratio": result["ratio"]
                        })
                        
                        if result["ratio"] > best_ratio:
                            best_ratio = result["ratio"]
                            best_x = x_pos
                            best_y = y_pos
                
                self.scan_results = sorted(results, key=lambda x: x["ratio"], reverse=True)[:10]
                
                # If we found good green, move towards it
                if best_ratio > self.green_threshold:
                    # Move closer to the green area
                    self.smooth_move_to(int(best_x), int(best_y))
                    self.current_x = int(best_x)
                    self.current_y = int(best_y)
                    self.target_found = True
                else:
                    self.target_found = False
                
                time.sleep(0.1)  # Scan every 100ms
                
            except Exception as e:
                time.sleep(1)
                continue
    
    def start_continuous_scan(self):
        """Start background scanning"""
        if not self.is_scanning:
            scan_thread = threading.Thread(target=self.continuous_scan, daemon=True)
            scan_thread.start()
            return True
        return False
    
    def stop_continuous_scan(self):
        """Stop background scanning"""
        self.is_scanning = False
        return True
    
    def quick_scan_around(self):
        """Quick scan around current position"""
        results = []
        for offset_x in range(-100, 101, 20):
            for offset_y in range(-50, 51, 20):
                x_pos = max(25, min(self.screen_width - 25, self.current_x + offset_x))
                y_pos = max(25, min(self.screen_height - 25, self.current_y + offset_y))
                
                region = (int(x_pos - 25), int(y_pos - 25), 50, 50)
                result = self.detect_green_precise(region)
                
                results.append({
                    "x": int(x_pos),
                    "y": int(y_pos),
                    "ratio": result["ratio"],
                    "offset_x": result["center_offset_x"],
                    "offset_y": result["center_offset_y"]
                })
        
        # Sort by green ratio
        results.sort(key=lambda x: x["ratio"], reverse=True)
        return results[:5]  # Return top 5

# Initialize bot
bot = EnhancedColorBot()

@app.route('/')
def home():
    return jsonify({
        "message": "Enhanced Color Bot Backend - 24/7 Operation",
        "status": "online",
        "version": "2.0"
    })

@app.route('/status')
def status():
    return jsonify({
        "current_position": {"x": int(bot.current_x), "y": int(bot.current_y)},
        "is_running": bot.is_running,
        "is_scanning": bot.is_scanning,
        "target_found": bot.target_found,
        "screen_size": {"width": int(bot.screen_width), "height": int(bot.screen_height)}
    })

@app.route('/start-scan', methods=['POST'])
def start_scan():
    success = bot.start_continuous_scan()
    return jsonify({
        "message": "Continuous scanning started" if success else "Already scanning",
        "success": success
    })

@app.route('/stop-scan', methods=['POST'])
def stop_scan():
    success = bot.stop_continuous_scan()
    return jsonify({
        "message": "Continuous scanning stopped" if success else "Was not scanning",
        "success": success
    })

@app.route('/quick-scan', methods=['GET'])
def quick_scan():
    results = bot.quick_scan_around()
    return jsonify({
        "message": "Quick scan complete",
        "results": results
    })

@app.route('/move-to/<int:x>/<int:y>', methods=['POST'])
def move_to_position(x, y):
    try:
        bot.smooth_move_to(int(x), int(y))
        bot.current_x = int(x)
        bot.current_y = int(y)
        return jsonify({"message": f"Moved to ({x}, {y})"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify({
            "scan_step": bot.scan_step,
            "scan_range": bot.scan_range,
            "green_threshold": bot.green_threshold,
            "smooth_movement": bot.smooth_movement
        })
    else:
        data = request.json
        if 'scan_step' in data:
            bot.scan_step = int(data['scan_step'])
        if 'scan_range' in data:
            bot.scan_range = int(data['scan_range'])
        if 'green_threshold' in data:
            bot.green_threshold = float(data['green_threshold'])
        if 'smooth_movement' in data:
            bot.smooth_movement = bool(data['smooth_movement'])
        return jsonify({"message": "Settings updated"})

if __name__ == '__main__':
    # Start continuous scanning automatically
    bot.start_continuous_scan()
    
    app.run(host='0.0.0.0', port=port)
