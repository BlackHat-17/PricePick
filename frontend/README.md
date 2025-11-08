# PricePick Frontend

React + TypeScript frontend for the PricePick price tracking application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Update `.env` with your backend URL:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

4. Start development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:8080`

## Features

- ✅ User Authentication (Login/Register)
- ✅ Product Management
- ✅ Price Tracking Dashboard
- ✅ Protected Routes
- ✅ API Integration with Backend
- ✅ Real-time Data Fetching with React Query

## Backend Connection

The frontend connects to the backend API at `http://localhost:8000/api/v1` by default.

Make sure:
1. Backend is running on port 8000
2. CORS is configured in backend to allow `http://localhost:8080`
3. Backend `.env` has `ALLOWED_ORIGINS` including `http://localhost:8080`

## API Endpoints Used

- `/users/register` - User registration
- `/users/login` - User login
- `/users/me` - Get current user
- `/products/` - List/create products
- `/products/{id}` - Get/update/delete product
- `/prices/` - List prices
- `/prices/product/{id}/history` - Get price history
- `/monitoring/alerts` - Manage price alerts

## Project Structure

```
src/
├── components/     # Reusable UI components
├── contexts/      # React contexts (Auth)
├── hooks/         # Custom React hooks
├── lib/           # Utilities and API client
├── pages/         # Page components
└── App.tsx        # Main app component
```
