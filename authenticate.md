
### SimpleTek

1. **Module Overview**
## Module :  Authenticate
**Base URL** : `/auth/`
**Description** : Handles user authentication process including login, logout, registration, password management, and maintains user logs.

2. **Models**
### Models

#### `PortalUser`
- **Fields**:
    - `company` (Foriegn key to Company model)
    - `designation` (Foriegn key to UserRoles model)
    - `mobile_number`
    - `phone_number`
- **Purpose**: Extends the default Django user model with additional user-specific data

#### `UserLogs`
- **Fields**:
    - `user` (Foreign key to PortalUser)
    - `description` (describe user activity) e.g user xyz@gmail.com logged in successfully!
- **Purpose**: describes user activity

3. **Endpoints (API)**

| Method        | URL                     | View            | Description                          | Auth Required |
|---------------|-------------------------|-----------------|--------------------------------------|---------------|
| POST          | /auth/register/         | RegisterView    | Register a new user                  | Yes           |
| POST          | /auth/login/            | LoginView       | Authenticate and return token        | No            |
| GET           | /auth/profile/          | ProfileView     | Get current user's profile           | Yes           |
| PUT/DELETE    | /auth/profile/<id>/     | ProfileView     | Update profile of user with ID       | Yes           |
| POST          | /auth/logout/           | LogoutView      | Logout user and invalidate session   | Yes           |
| GET           | /auth/user-logs/        | UserLogView     | List all user logs                   | Yes (Admin)   |
| GET/DELETE    | /auth/user-logs/<id>/   | UserLogView     | Retrieve user log by ID              | Yes (Admin)   |



