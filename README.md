# Automated Retail Billing System with Real-Time Object Detection

## Project Overview
This project is an automated retail billing system that uses real-time object detection to identify products via a camera and generate a bill automatically. It leverages a YOLOv8 model for object detection and provides a web-based GUI for live monitoring, billing, and receipt generation.

## Features
- Real-time object detection using a webcam and YOLOv8
- Automatic item counting and billing
- Web-based GUI for live video feed and bill display
- PDF receipt generation
- Customizable product prices

## Folder Structure
- `src/` - Main source code
  - `main.py` - Flask web server and GUI logic
  - `object_billing.py` - Core object detection and billing logic
  - `config/prices.json` - Product price configuration (edit as needed)
  - `utils/` - Utility modules
- `models/yolo/last.pt` - Trained YOLOv8 model weights
- `output/receipts/` - Generated PDF receipts
- `static/` - Static files (CSS, JS, images)
- `templates/` - HTML templates for the web interface
- `requirements.txt` - Python dependencies

## Setup Instructions

### 1. Clone the Repository
```
git clone <repo-url>
cd main_file_with_gui
```

### 2. Install Dependencies
It is recommended to use a virtual environment:
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download/Place YOLOv8 Model
- Place your trained YOLOv8 model weights as `models/yolo/last.pt`.
- You can train your own model using [Ultralytics YOLO](https://docs.ultralytics.com/).

### 4. Configure Product Prices (Optional)
- Edit `src/config/prices.json` to set custom prices for detected products.
- If the file is empty or missing, default prices will be used.

### 5. Run the Application
```
python src/main.py
```
- The web interface will be available at [http://localhost:5000](http://localhost:5000)

## Usage
- The camera feed will show detected items and the current bill.
- Use the web interface to generate a PDF receipt or reset the bill.
- Excluded items (e.g., "kissan mixed fruit jam") can be configured in `main.py`.

## Requirements
- Python 3.8+
- Webcam
- Windows OS (tested)

## Dependencies
See `requirements.txt`:
- ultralytics
- opencv-python
- reportlab
- flask
- numpy

## License
MIT License

## Acknowledgements
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- OpenCV
- Flask
- ReportLab
