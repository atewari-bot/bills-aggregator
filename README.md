# Bills Analyzer & Aggregator

A full-stack application for uploading, analyzing, and tracking bills. Upload bill images (with OCR scanning) or CSV files, and get detailed monthly breakdowns by shop, items, and categories.

## Features

1. **Bill Image Upload**: Upload photos of bills and automatically extract line items using OCR
2. **CSV Upload**: Upload CSV files with manual bill entries
3. **Monthly Analysis**: Detailed breakdown of spending by:
   - Shop name
   - Item categories
   - Individual items
4. **Persistent Storage**: All bills and line items are saved to a SQLite database
5. **Visual Dashboard**: Beautiful charts and tables showing spending patterns

## Tech Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: ORM for database operations
- **Pytesseract**: OCR for extracting text from bill images
- **SQLite**: Database for persistent storage

### Frontend
- **React**: UI library
- **Chart.js**: Data visualization
- **Axios**: HTTP client

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- Tesseract OCR (optional, for image scanning)

#### Installing Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
python app.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

### Uploading Bill Images

1. Click on "Upload Bills" section
2. Select "Image" upload type
3. Click "Click to upload bill image"
4. Select a photo of your bill
5. The app will automatically scan and extract line items

**Note**: If Tesseract OCR is not installed, the app will use mock data for demonstration purposes.

### Uploading CSV Files

1. Click on "Upload Bills" section
2. Select "CSV" upload type
3. Click "Click to upload CSV file"
4. Upload a CSV file with the following format:

```csv
shop_name,date,total_amount,line_items
Walmart,2024-01-15,45.67,"Milk 2L,1,3.99,Groceries|Bread,2,2.50,Groceries|Eggs Dozen,1,4.99,Groceries"
Target,2024-01-16,28.50,"Shampoo,1,6.75,Personal Care|Toilet Paper,1,9.99,Household|Snacks,3,3.96,Snacks"
```

**CSV Format:**
- `shop_name`: Name of the shop/store
- `date`: Date in YYYY-MM-DD format
- `total_amount`: Total bill amount
- `line_items`: Pipe-separated (`|`) list of items, each item format: `name,quantity,price,category`

### Viewing Analysis

1. Select the month and year using the filters
2. View the dashboard with:
   - Summary cards (total spent, bills count, etc.)
   - Charts for spending by shop and category
   - Tables with detailed breakdowns
   - List of all bills

## API Endpoints

### `GET /api/health`
Health check endpoint

### `POST /api/bills/upload-image`
Upload a bill image file
- **Body**: multipart/form-data with `file` field
- **Returns**: Created bill with extracted line items

### `POST /api/bills/upload-csv`
Upload a CSV file with bill data
- **Body**: multipart/form-data with `file` field
- **Returns**: List of created bills

### `GET /api/bills`
Get all bills (optional filters: `month`, `year`)
- **Query params**: `month` (int), `year` (int)
- **Returns**: List of bills with line items

### `GET /api/analysis/monthly`
Get monthly analysis
- **Query params**: `month` (int), `year` (int) - required
- **Returns**: Analysis breakdown by shop, category, and items

### `GET /api/analysis/summary`
Get summary statistics
- **Query params**: `month` (int), `year` (int) - optional
- **Returns**: Summary statistics

## Project Structure

```
bills-aggregator/
├── backend/
│   ├── app.py                 # Flask application
│   ├── models.py              # Database models
│   ├── requirements.txt      # Python dependencies
│   ├── services/
│   │   ├── ocr_service.py    # OCR service for image scanning
│   │   └── analysis_service.py # Analysis service
│   └── uploads/              # Uploaded files directory
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js            # Main app component
│   │   ├── components/       # React components
│   │   └── services/         # API service
│   └── package.json
├── README.md
└── .gitignore
```

## Development

### Database

The app uses SQLite by default. The database file `bills.db` will be created automatically in the backend directory.

To reset the database, simply delete `bills.db` and restart the backend server.

### OCR Configuration

The OCR service will automatically check for Tesseract availability. If not available, it uses mock data for demonstration. For production use, ensure Tesseract is properly installed and configured.

## Future Enhancements

- Support for PDF bill uploads
- Advanced OCR with better accuracy
- User authentication and multi-user support
- Export analysis reports (PDF, Excel)
- Budget tracking and alerts
- Recurring bill detection
- Mobile app support

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
