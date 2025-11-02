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

You can run the application using Docker (recommended) or install it locally.

### Option 1: Docker (Recommended)

#### Prerequisites
- Docker Desktop or Docker Engine 20.10+
- Docker Compose 2.0+

#### Quick Start with Docker

```bash
# Build and start the application
docker-compose up --build

# Or use Makefile commands
make start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

#### Development Mode with Docker

```bash
# Start development environment with hot-reload
docker-compose -f docker-compose.dev.yml up --build

# Or use Makefile
make start-dev
```

#### Docker Commands

```bash
# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose build --no-cache

# Clean up volumes and containers
make clean
```

### Option 2: Local Installation

#### Prerequisites

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
4. Upload a CSV file in one of the supported formats:

#### Format 1: Bill Summary Format

Each row represents a complete bill:

```csv
shop_name,date,total_amount,line_items
Walmart,2024-01-15,45.67,"Milk 2L,1,3.99,Groceries|Bread,2,2.50,Groceries|Eggs Dozen,1,4.99,Groceries"
Target,2024-01-16,28.50,"Shampoo,1,6.75,Personal Care|Toilet Paper,1,9.99,Household|Snacks,3,3.96,Snacks"
```

**Columns:**
- `shop_name`: Name of the shop/store
- `date`: Date in YYYY-MM-DD format
- `total_amount`: Total bill amount
- `line_items`: Pipe-separated (`|`) list of items, each item format: `name,quantity,price,category`

#### Format 2: Line Item Format (Recommended)

Each row represents a single line item. The app automatically groups items by date and shop:

```csv
Item Name,Item Type,Item Sub Type,Quantity,Unit measure,Cost per unit,Total amount paid,Date,Shop Address
Strawberries,Grocery,Fruit,2,NA,$7.99,$15.98,02/09/2025,Costco Wholesale
Mustard Oil,Grocery,Oil,5,liters,NA,$17.99,2/15/2025,Apni Mandi
```

**Columns:**
- `Item Name`: Name of the item
- `Item Type`: Main category (e.g., Grocery, Apparel)
- `Item Sub Type`: Sub-category (e.g., Fruit, Vegetable)
- `Quantity`: Quantity purchased
- `Unit measure`: Unit of measurement (lb, liters, etc.)
- `Cost per unit`: Price per unit (optional)
- `Total amount paid`: Total price for this item
- `Date`: Purchase date (supports formats: MM/DD/YYYY, YYYY-MM-DD)
- `Shop Address`: Name/address of the shop

The app will automatically:
- Group items by Date and Shop Address to create bills
- Calculate total bill amount from line items
- Categorize items based on Item Sub Type or Item Type

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
│   ├── Dockerfile             # Backend Docker image
│   ├── app.py                 # Flask application
│   ├── models.py              # Database models
│   ├── requirements.txt      # Python dependencies
│   ├── services/
│   │   ├── ocr_service.py    # OCR service for image scanning
│   │   └── analysis_service.py # Analysis service
│   └── uploads/              # Uploaded files directory
├── frontend/
│   ├── Dockerfile             # Frontend production Docker image
│   ├── Dockerfile.dev         # Frontend development Docker image
│   ├── nginx.conf             # Nginx configuration for production
│   ├── public/
│   ├── src/
│   │   ├── App.js            # Main app component
│   │   ├── components/       # React components
│   │   └── services/         # API service
│   └── package.json
├── docker-compose.yml         # Production Docker Compose
├── docker-compose.dev.yml     # Development Docker Compose
├── Makefile                   # Convenience commands
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
