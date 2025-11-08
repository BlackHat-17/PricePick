# JWT Authentication Implementation

## Overview

JWT (JSON Web Token) authentication has been fully implemented for the PricePick application, allowing users to sign up and log in securely.

## Backend Implementation

### Files Created/Modified

1. **`backend/app/dependencies.py`** (NEW)
   - `get_current_user()` - Dependency to extract user from JWT token
   - `get_current_active_user()` - Dependency to get active user only
   - `get_optional_user()` - Optional user dependency

2. **`backend/app/routes/users.py`** (UPDATED)
   - `/users/register` - Now returns JWT token after registration
   - `/users/login` - Enabled and returns JWT token
   - `/users/me` - Protected route requiring JWT authentication
   - `/users/me` (PUT) - Protected route for updating user profile
   - `/users/logout` - Logout endpoint (client-side token removal)

3. **`backend/app/schemas/user.py`** (UPDATED)
   - Updated validators to use Pydantic v2 `field_validator`
   - Relaxed password requirements (minimum 6 characters)
   - Added computed `full_name` field

### Authentication Flow

1. **Registration**:
   ```
   POST /api/v1/users/register
   Body: { username, email, password }
   Response: { access_token, token_type, expires_in, user }
   ```

2. **Login**:
   ```
   POST /api/v1/users/login
   Body: { username, password }
   Response: { access_token, token_type, expires_in, user }
   ```

3. **Get Current User**:
   ```
   GET /api/v1/users/me
   Headers: { Authorization: Bearer <token> }
   Response: { user object }
   ```

4. **Update User**:
   ```
   PUT /api/v1/users/me
   Headers: { Authorization: Bearer <token> }
   Body: { ...user fields }
   Response: { updated user object }
   ```

### JWT Token Details

- **Algorithm**: HS256
- **Expiration**: Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30 minutes)
- **Token Payload**:
  - `user_id`: User ID
  - `exp`: Expiration timestamp
  - `iat`: Issued at timestamp
  - `type`: "access"

## Frontend Implementation

### Files Modified

1. **`frontend/src/lib/api.ts`**
   - Updated `TokenResponse` interface to include `user` and `expires_in`
   - Updated `register()` to return `TokenResponse` instead of `User`
   - Token is automatically stored in localStorage

2. **`frontend/src/contexts/AuthContext.tsx`**
   - Updated `register()` to handle token response
   - Auto-navigates to dashboard after registration

3. **`frontend/src/pages/Login.tsx`**
   - Already connected to backend login API
   - Handles JWT token storage

4. **`frontend/src/pages/Signup.tsx`**
   - Already connected to backend registration API
   - Handles JWT token storage

### Token Storage

- Tokens are stored in `localStorage` with key `auth_token`
- Token is automatically included in API requests via `Authorization: Bearer <token>` header
- Token is removed on logout

## Usage

### Backend

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. The API will be available at `http://localhost:8000`

### Frontend

1. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

2. Access the app at `http://localhost:8080`

3. Test authentication:
   - Go to `/signup` to create an account
   - Go to `/login` to sign in
   - Protected routes (dashboard, products) require authentication

## Security Features

- ✅ Password hashing using bcrypt
- ✅ JWT token expiration
- ✅ Account lockout after failed login attempts
- ✅ Token validation on every protected request
- ✅ CORS configured for frontend origins

## Password Requirements

- Minimum 6 characters (relaxed from previous strict requirements)
- No special character requirements

## Testing

You can test the authentication using:

1. **Swagger UI**: `http://localhost:8000/docs`
   - Try the `/users/register` and `/users/login` endpoints
   - Use "Authorize" button to add Bearer token for protected endpoints

2. **Frontend**: Use the login/signup forms

3. **cURL**:
   ```bash
   # Register
   curl -X POST http://localhost:8000/api/v1/users/register \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

   # Login
   curl -X POST http://localhost:8000/api/v1/users/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"password123"}'

   # Get current user (use token from login response)
   curl -X GET http://localhost:8000/api/v1/users/me \
     -H "Authorization: Bearer <your_token_here>"
   ```

## Next Steps

- [ ] Add refresh token support
- [ ] Add password reset functionality
- [ ] Add email verification
- [ ] Add rate limiting for authentication endpoints
- [ ] Add token blacklist for logout (if needed)

