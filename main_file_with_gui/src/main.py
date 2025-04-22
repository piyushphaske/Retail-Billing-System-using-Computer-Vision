import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
from src.object_billing import ObjectBillingSystem
import numpy as np
import signal

app = Flask(__name__, 
    template_folder='../templates',
    static_folder='../static')

# Initialize the billing system
model_path = "models/yolo/last.pt"
billing_system = ObjectBillingSystem(model_path=model_path, confidence=0.5, time_threshold=5.0)

# Define items to exclude from detection
excluded_items = ["kissan mixed fruit jam"]

# Monkey patch the process_frame method to skip kissan jam
original_process_frame = billing_system.process_frame

def filtered_process_frame(self, frame):
    # Store current items state
    current_items = self.items.copy()
    
    # Call the original method
    processed_frame = original_process_frame(frame)
    
    # Remove the excluded items from tracking/counting
    for item in excluded_items:
        if item in self.items:
            # Restore previous count for this item (effectively ignoring it)
            if item in current_items:
                self.items[item] = current_items[item]
            else:
                # If it wasn't there before, remove it completely
                del self.items[item]
    
    return processed_frame

# Apply the monkey patch
billing_system.process_frame = filtered_process_frame.__get__(billing_system, ObjectBillingSystem)

# Global variables for sharing camera frames and bill data
frame_buffer = None
last_frame_time = 0

def camera_thread():
    """Background thread that captures frames and processes them"""
    global frame_buffer, last_frame_time
    print("Starting camera thread...")
    
    # Try different backends
    print("Attempting to open camera with DirectShow backend...")
    # Try different backends
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Try DirectShow backend on Windows
    
    if not cap.isOpened():
        print("Failed to open camera with DirectShow, trying default...")
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Failed to open camera with index 0, trying index 1...")
        cap = cv2.VideoCapture(1)
        
    if not cap.isOpened():
        print("All camera attempts failed. Using a placeholder image instead.")
        # Use a placeholder image
        placeholder = np.ones((480, 640, 3), dtype=np.uint8) * 200  # Gray image
        cv2.putText(placeholder, "Camera not available", (100, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        while True:
            # Process placeholder instead
            processed_frame = billing_system.process_frame(placeholder)
            _, buffer = cv2.imencode('.jpg', processed_frame)
            frame_buffer = buffer.tobytes()
            last_frame_time = time.time()
            time.sleep(0.1)
    
    # If camera opened successfully, continue with normal operation
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            time.sleep(0.1)
            continue
        
        # Process the frame with your detection system
        processed_frame = billing_system.process_frame(frame)
        
        # Encode as JPEG for streaming
        _, buffer = cv2.imencode('.jpg', processed_frame)
        frame_buffer = buffer.tobytes()
        last_frame_time = time.time()
        
        # Slight delay to reduce CPU usage
        time.sleep(0.01)

# Route for the main page
@app.route('/terminate_program')
def terminate_program():
    # Get the current process ID
    pid = os.getpid()
    # Send a shutdown signal to the Flask app (will be caught in the main thread)
    os.kill(pid, signal.SIGTERM)
    return jsonify({"success": True, "message": "Program terminating..."})

@app.route('/')
def index():
    return render_template('index.html')

# Route for video feed
@app.route('/video_feed')
def video_feed():
    def generate_frames():
        global frame_buffer, last_frame_time
        
        while True:
            # Add a timeout check to avoid hanging if frame_buffer is None
            if frame_buffer is None:
                # Create a simple placeholder frame
                placeholder = np.ones((480, 640, 3), dtype=np.uint8) * 200
                cv2.putText(placeholder, "Waiting for camera...", (100, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                _, buffer = cv2.imencode('.jpg', placeholder)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_buffer + b'\r\n')
            time.sleep(0.03)  # ~30 FPS
            
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# API to get current bill data
@app.route('/api/current_bill')
def get_current_bill():
    items_list = []
    total = 0
    
    for cls_name, item_info in billing_system.items.items():
        # Skip excluded items in the bill as well
        if item_info["count"] > 0 and cls_name not in excluded_items:
            price = billing_system.prices.get(cls_name, 0)
            amount = item_info["count"] * price
            total += amount
            
            items_list.append({
                "name": cls_name,
                "quantity": item_info["count"],
                "unit_price": price,
                "total": amount
            })
    
    return jsonify({
        "items": items_list,
        "subtotal": total,
        "tax": total * 0.07,  # 7% tax as in your code
        "total": total * 1.07
    })

@app.route('/generate_receipt')
def generate_receipt():
    # Make sure excluded items don't appear in the receipt
    original_items = billing_system.items.copy()
    for item in excluded_items:
        if item in billing_system.items:
            del billing_system.items[item]
            
    filename = billing_system.generate_bill_pdf("output/receipts/receipt.pdf")
    
    # Restore original items
    billing_system.items = original_items
    return jsonify({"success": True, "filename": filename})

# Route to reset the bill
@app.route('/reset_bill')
def reset_bill():
    billing_system.items.clear()
    return jsonify({"success": True})

if __name__ == "__main__":
    print(f"Starting with excluded items: {excluded_items}")
    
    # Start the camera thread
    thread = threading.Thread(target=camera_thread)
    thread.daemon = True
    thread.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)