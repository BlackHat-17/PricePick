# PricePick Backend

A comprehensive price tracking and monitoring system inspired by iShopBot, built with FastAPI and Python.

## Features

- **Product Management**: Add, update, and track products from multiple e-commerce platforms
- **Price Monitoring**: Automated price tracking with configurable intervals
- **Price Alerts**: Set up alerts for price drops, increases, or target prices
- **Web Scraping**: Extract product data from e-commerce websites
- **User Management**: User authentication and authorization
- **API**: RESTful API with comprehensive endpoints
- **Background Tasks**: Automated price monitoring and alert checking
- **Notifications**: Email, push, and SMS notifications (configurable)

## Supported Platforms

- Amazon
- eBay
- Walmart
- Target
- Best Buy
- Home Depot
- Lowe's

## Quick Start

### Prerequisites

- Python 3.8+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pricepick/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment configuration:
```bash
cp env.example .env
```

5. Update the `.env` file with your configuration.

6. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   ├── schemas/         # Pydantic schemas
│   ├── database/        # Database configuration
│   ├── tasks/           # Background tasks
│   └── utils/           # Utility functions
├── tests/               # Test files
├── main.py             # Application entry point
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Configuration

The application can be configured through environment variables. See `env.example` for all available options.

### Key Configuration Options

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key for authentication
- `PRICE_CHECK_INTERVAL`: How often to check prices (in seconds)
- `MAX_PRICE_HISTORY_DAYS`: How long to keep price history
- `ENABLE_EMAIL_NOTIFICATIONS`: Enable/disable email notifications

## API Endpoints

### Products
- `GET /api/v1/products/` - List products
- `POST /api/v1/products/` - Create product
- `GET /api/v1/products/{id}` - Get product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product
- `POST /api/v1/products/{id}/scrape` - Manually scrape product

### Prices
- `GET /api/v1/prices/` - List prices
- `GET /api/v1/prices/product/{id}/history` - Get price history
- `GET /api/v1/prices/trends/popular` - Get popular trends
- `GET /api/v1/prices/alerts/price-drops` - Get price drops

### Users
- `POST /api/v1/users/register` - Register user
- `POST /api/v1/users/login` - Login user
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user

### Monitoring
- `POST /api/v1/monitoring/alerts` - Create price alert
- `GET /api/v1/monitoring/alerts` - List alerts
- `PUT /api/v1/monitoring/alerts/{id}` - Update alert
- `DELETE /api/v1/monitoring/alerts/{id}` - Delete alert

## Background Tasks

The application includes several background tasks:

1. **Price Monitoring**: Checks product prices at regular intervals
2. **Alert Checking**: Evaluates price alerts and triggers notifications
3. **Data Cleanup**: Removes old data to maintain performance

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## Development

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run formatting:

```bash
black .
isort .
```

Run linting:

```bash
flake8 .
mypy .
```

## Deployment

### Production Considerations

1. **Database**: Use PostgreSQL or MySQL for production
2. **Security**: Change the SECRET_KEY and use HTTPS
3. **Monitoring**: Set up logging and monitoring
4. **Scaling**: Use a reverse proxy like Nginx
5. **Background Tasks**: Consider using Celery with Redis

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub.
