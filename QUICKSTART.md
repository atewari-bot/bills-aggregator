# Quick Start Guide

Get the Bills Analyzer & Aggregator up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm (comes with Node.js)

## Installation Steps

### Option 1: Automated Setup (Recommended)

Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

#### 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Step 1: Start the Backend

Open a terminal and run:

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

### Step 2: Start the Frontend

Open another terminal and run:

```bash
cd frontend
npm start
```

The browser should automatically open to `http://localhost:3000`

## First Steps

1. **Upload a CSV file**: Use the provided `sample_bills.csv` file to test the CSV upload feature
2. **Upload a bill image**: Try uploading a photo of a receipt (OCR will extract the data)
3. **View Analysis**: Select a month/year using the filters and see your spending breakdown

## Testing with Sample Data

A sample CSV file (`sample_bills.csv`) is included in the root directory. You can upload it to see the application in action with sample data.

## Troubleshooting

### Backend won't start

- Make sure you're in the `backend` directory
- Ensure the virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start

- Make sure you're in the `frontend` directory
- Ensure Node.js is installed: `node --version`
- Try deleting `node_modules` and running `npm install` again

### OCR not working

- The app includes mock data if Tesseract OCR is not installed
- For real OCR, install Tesseract:
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`
  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

### Port already in use

- Backend: Change port in `backend/app.py` (default: 5000)
- Frontend: React will prompt to use a different port if 3000 is taken

## Next Steps

- Explore the monthly analysis dashboard
- Upload your own bills
- Try different months and years using the filters

Enjoy analyzing your bills! 📊

