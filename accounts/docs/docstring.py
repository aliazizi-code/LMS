GENERATE_OTP_DESC = """
This endpoint generates a 6-digit One Time Password (OTP) and sends it to the provided phone number.

### Key Features:
- Validates phone number format
- Generates cryptographically secure OTP
- Stores OTP in cache with expiration time
- Sends OTP via SMS using Celery task

### Validation Rules:
- Phone number must be in E.164 format
- Example valid number: +989123456789O
- Minimum length: 12 characters
- Maximum length: 13 characters

### Security:
- Rate limited to 1 request per minute
- OTP expires after 1 minutes
- Exceeding 1 request per minute results in 403 Forbidden
"""

VERIFY_OTP_DESC = """
This endpoint generates a 6-digit One Time Password (OTP) and sends it to the provided phone number.

### Key Features:
- Validates OTP against cached value
- Authenticates user upon successful verification
- Issues JWT tokens (access + refresh)
- Handles both new and existing user cases
- Updates user authentication status

### Validation Rules:
- OTP must be 6 digits exactly
- OTP must match the cached value
- Phone number must match the OTP request

### Security:
- OTP expires after 1 minutes
- Automatic token rotation on successful verification
- CSRF token rotation on authentication


### Token Configuration:
- Access tokens: 15 minutes validity (requires refresh after expiration)
- Refresh tokens: 30 days validity (allows obtaining new access tokens)
- Authentication: Bearer token (Authorization: Bearer <token>)
"""

REFRESH_TOKEN_DESC = """
### Technical Details:
- Uses refresh token rotation
- Updates CSRF token automatically
- Invalidates previous refresh tokens
- Token blacklisting support

### Token Configuration:
- Access tokens: 15 minutes validity (requires refresh after expiration)
- Refresh tokens: 30 days validity (allows obtaining new access tokens)
- Authentication: Bearer token (Authorization: Bearer <token>)
"""

LOGOUT_DESC = """
### Technical Implementation:
1. Adds refresh token to blacklist
2. Deletes authentication cookies
3. Generates new CSRF token
4. Clears session data
"""

USER_PROFILE_RETRIEVE_DESC = """
- Basic user info (first name, last name, email, phone)
- Profile details (bio, job, gender, age)
- Avatar and thumbnail URLs

### Technical Notes:
- Only accessible to authenticated users
- Email and phone fields are read-only
- Automatically creates profile if it doesn't exist
"""

USER_PROFILE_UPDATE_DESC = """
#### Updatable Fields:
- first_name (optional)
- last_name (required)
- bio (optional)
- job (optional)
- avatar (optional)
- age (optional)
- gender (optional)

#### Restrictions:
- Email and phone fields are immutable
- Max avatar size: 2MB
- Allowed formats: JPG, PNG

### Technical Notes:
- Use PATCH method
- Atomic update on both User and UserProfile models
"""

CHANGE_PHONE_REQUEST_DESC = """
This endpoint initiates phone number change by sending OTP.

### Key Features:
- Validates phone number format (E.164)
- Checks for duplicate numbers
- Generates secure 6-digit OTP
- Sends OTP via SMS using Celery

### Security:
- Rate limited to 1 request per minute
- OTP expires after 1 minutes
- Exceeding 1 request per minute results in 403 Forbidden
"""

CHANGE_PHONE_VERIFY_DESC = """
This endpoint verifies OTP and completes phone number change.

### Key Features:
- Validates OTP against cached value
- Updates user's phone number
- Requires original phone number used in request

### Security:
- OTP expires after 1 minutes
- Invalidates OTP after use
- Rejects mismatched phone numbers
- Requires authentication
"""

CHANGE_EMAIL_REQUEST_DESC = """
This endpoint initiates email change by sending verification email.

### Key Features:
- Validates email format
- Checks for duplicate emails
- Generates secure verification token
- Sends email via Celery task

### Security:
- Token expires after 24 hours
- Only one active token per user
- Rejects unverified emails
"""

CHANGE_EMAIL_VERIFY_DESC = """
This endpoint verifies token and completes email change.

### Key Features:
- Validates token against database
- Updates user's email
- Requires original verification token

### Security:
- Single-use token
- Immediately invalid after use
"""
