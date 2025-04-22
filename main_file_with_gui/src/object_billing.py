import cv2
import time
import os
import json
import numpy as np
from collections import defaultdict
from ultralytics import YOLO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import datetime

class ObjectBillingSystem:
    def __init__(self, model_path, confidence=0.5, time_threshold=5.0):
        """
        Initialize the real-time object detection and billing system
        
        Args:
            model_path (str): Path to the trained YOLOv8 model
            confidence (float): Confidence threshold for detections
            time_threshold (float): Time in seconds to increment quantity counter
        """
        # Dictionary to store item counts and their last seen timestamps
        self.items = defaultdict(lambda: {
            "count": 0, 
            "last_seen": 0, 
            "continuous_time": 0,
            "last_added_time": 0  # Track when the item was last added to the bill
        })

        # Load the YOLO model
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.time_threshold = time_threshold
        
        # Get class names from model
        self.class_names = self.model.names
        
        # Load product prices from JSON file
        self.prices = self._load_prices()
        
        # Add default prices for any classes not in the price list
        for class_id, class_name in self.class_names.items():
            if class_name not in self.prices:
                self.prices[class_name] = 2.00  # Default price for unknown items

    def _load_prices(self):
        """Load product prices from JSON file"""
        price_file = os.path.join(os.path.dirname(__file__), 'config', 'prices.json')
        
        # If price file exists, load it
        if os.path.exists(price_file):
            try:
                with open(price_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading prices from {price_file}: {e}")
        
        # Fallback to default prices
        return {
            'apple': 20,
            'Blue bottle': 100,
            'nivea': 50,
            'parachute hair oil': 60,
            'Nivea Facewash': 30,
            'Moong Dal': 40,
            'Colgate Toothpaste': 70,
            'Kissan mixed fruit jam': 80
        }

    def generate_bill_pdf(self, filename="receipt.pdf"):
        """Generate a PDF bill with the detected items"""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Get current date and time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a PDF document
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add header
        header = Paragraph("<b>Retail Billing Receipt</b>", styles["Title"])
        elements.append(header)
        
        # Add date and time
        date_time = Paragraph(f"Date: {current_time}", styles["Normal"])
        elements.append(date_time)
        elements.append(Paragraph("<br/><br/>", styles["Normal"]))
        
        # Create data for table
        data = [['Item', 'Quantity', 'Unit Price', 'Total']]
        total_amount = 0
        
        # Debug - print all items with their counts before generating bill
        print("\nItems in bill:")
        for cls_name, item_info in self.items.items():
            print(f"- {cls_name}: count={item_info['count']}")
        
        # Add items to the bill
        items_added = False
        for cls_name, item_info in dict(self.items).items():
            if item_info["count"] > 0:
                items_added = True
                unit_price = self.prices.get(cls_name, 0)
                total_price = unit_price * item_info["count"]
                total_amount += total_price
                
                data.append([
                    cls_name, 
                    str(item_info["count"]), 
                    f"{unit_price:.2f}", 
                    f"{total_price:.2f}"
                ])
        
        # If no items were added, show a placeholder
        if not items_added:
            print("Warning: No items with count > 0 found")
            data.append(['No items detected', '0', '0.00', '0.00'])
        
        # Add subtotal, tax, and total
        tax_rate = 0.07  # 7% tax rate
        tax_amount = total_amount * tax_rate
        final_total = total_amount + tax_amount
        
        data.append(['', '', 'Subtotal:', f"{total_amount:.2f}"])
        data.append(['', '', 'Tax (7%):', f"{tax_amount:.2f}"])
        data.append(['', '', 'Total:', f"{final_total:.2f}"])
        
        # Create table and set style
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Paragraph("<br/><br/>Thank you for shopping with us!", styles["Normal"]))
        
        # Build PDF
        doc.build(elements)
        print(f"Receipt generated: {filename}")
        return filename
    
    def process_frame(self, frame):
        """Process a single frame for object detection and tracking"""
        current_time = time.time()
        
        # Run YOLOv8 inference on the frame
        results = self.model(frame, conf=self.confidence)
        
        # Get detected objects from this frame
        detected_items = set()
        
        # Process the results
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Get class ID and confidence
                cls_id = int(box.cls[0].item())
                conf = box.conf[0].item()
                
                # Get class name
                cls_name = self.class_names[cls_id]
                
                # Skip apple class
                if cls_name.lower() == 'apple':
                    continue
                    
                detected_items.add(cls_name)
                
                # Draw bounding box on frame
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Add label
                label = f"{cls_name}: {conf:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Update item tracking and counts
        for cls_name in list(self.items.keys()) + list(detected_items):
            # Initialize if not exists
            if cls_name not in self.items:
                self.items[cls_name] = {
                    "count": 0, 
                    "last_seen": 0, 
                    "continuous_time": 0,
                    "last_added_time": 0
                }
                
            if cls_name in detected_items:
                # Item is currently visible
                if self.items[cls_name]["last_seen"] == 0:
                    # First time seeing this item in this sequence
                    self.items[cls_name]["last_seen"] = current_time
                    self.items[cls_name]["continuous_time"] = 0
                else:
                    # Calculate continuous visibility time
                    elapsed = current_time - self.items[cls_name]["last_seen"]
                    self.items[cls_name]["continuous_time"] += elapsed
                    self.items[cls_name]["last_seen"] = current_time
                    
                    # Check if the cooldown period has elapsed since last adding this item
                    cooldown_elapsed = current_time - self.items[cls_name]["last_added_time"]
                    
                    # If continuously visible for more than threshold AND cooldown has elapsed, increment count
                    if (self.items[cls_name]["continuous_time"] >= self.time_threshold and 
                        (self.items[cls_name]["last_added_time"] == 0 or cooldown_elapsed >= self.time_threshold)):
                        print(f"Adding {cls_name} to bill - visible for {self.items[cls_name]['continuous_time']:.2f} seconds")
                        self.items[cls_name]["count"] += 1
                        self.items[cls_name]["continuous_time"] = 0  # Reset timer after incrementing
                        self.items[cls_name]["last_added_time"] = current_time  # Update last added time
            else:
                # Item is not visible in this frame
                if self.items[cls_name]["last_seen"] > 0:
                    # Item just disappeared
                    elapsed = current_time - self.items[cls_name]["last_seen"]
                    total_visible_time = self.items[cls_name]["continuous_time"] + elapsed
                    
                    # Check cooldown
                    cooldown_elapsed = current_time - self.items[cls_name]["last_added_time"]
                    
                    # If visible for less than threshold but greater than 0 AND cooldown has elapsed, count as 1
                    if (0 < total_visible_time < self.time_threshold and 
                        self.items[cls_name]["continuous_time"] > 0 and
                        (self.items[cls_name]["last_added_time"] == 0 or cooldown_elapsed >= self.time_threshold)):
                        print(f"Adding {cls_name} to bill - disappeared after {total_visible_time:.2f} seconds")
                        self.items[cls_name]["count"] += 1
                        self.items[cls_name]["last_added_time"] = current_time  # Update last added time
                    
                    # Reset tracking for this item
                    self.items[cls_name]["last_seen"] = 0
                    self.items[cls_name]["continuous_time"] = 0
        
        # Add billing information to the display
        y_offset = 30
        cv2.putText(frame, "Current Bill:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        y_offset += 30
        
        total_amount = 0
        for cls_name, item_info in self.items.items():
            if item_info["count"] > 0:
                amount = item_info["count"] * self.prices.get(cls_name, 0)
                total_amount += amount
                cv2.putText(frame, f"{cls_name}: {item_info['count']} x {self.prices.get(cls_name, 0):.2f} = {amount:.2f}", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                y_offset += 25
        
        cv2.putText(frame, f"Total: {total_amount:.2f}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
    
    def run(self):
        """Run the real-time object detection and billing system"""
        print("Starting real-time object detection and billing system...")
        print("Press 'q' to quit and generate bill.")
        print("Press 'r' to reset current bill.")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)  # Use 0 for primary webcam
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame from camera.")
                    break
                
                # Process the frame
                processed_frame = self.process_frame(frame)
                
                # Display the result
                cv2.imshow("Object Billing System", processed_frame)
                
                # Check for key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    # Generate bill and exit
                    print("Generating bill and exiting...")
                    self.generate_bill_pdf("output/receipts/receipt.pdf")
                    break
                elif key == ord('r'):
                    # Reset bill
                    print("Resetting current bill...")
                    self.items.clear()
        
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            # Release resources
            print("Releasing resources...")
            if cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()
            print("Resources released. Program terminated.")


if __name__ == "__main__":
    # Path to your trained YOLOv8 model
    model_path = "models/yolo/last.pt"
    
    # Create and run the object billing system
    billing_system = ObjectBillingSystem(
        model_path=model_path,
        confidence=0.5,
        time_threshold=5.0
    )
    
    billing_system.run()