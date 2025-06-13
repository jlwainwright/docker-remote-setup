# CyberZapend API Documentation

## Overview

CyberZapend provides a RESTful API for managing prepaid electricity vending through the CyberVendIT system. The API supports user authentication, property management, meter management, and electricity token generation.

**Base URL**: `http://localhost:8000`  
**Authentication**: Bearer Token (JWT)  
**Content-Type**: `application/json`

## Authentication

### POST /api/auth/login
**Purpose**: Authenticate user with email/password

**Request Body**:
```json
{
  "username": "admin@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes**:
- `200`: Success
- `401`: Invalid credentials
- `400`: Inactive user

---

### POST /api/auth/google/callback
**Purpose**: Authenticate user with Google OAuth

**Request Body**:
```json
{
  "code": "google_authorization_code"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid authorization code
- `409`: Email already exists with different account

---

### GET /api/auth/me
**Purpose**: Get current authenticated user information

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "id": 1,
  "email": "admin@example.com",
  "name": "Admin User",
  "google_id": "google_oauth_sub_id",
  "is_active": true,
  "role": "Admin",
  "created_at": "2024-12-27T10:00:00Z",
  "updated_at": "2024-12-27T10:00:00Z"
}
```

**Status Codes**:
- `200`: Success
- `401`: Invalid or expired token

## Properties

### GET /api/properties
**Purpose**: Get list of all properties

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
[
  {
    "id": 1,
    "name": "11 Jansen Van Rensburg Street",
    "config_key": "11_jansen_van_rensburg_street",
    "address": "11 Jansen Van Rensburg Street",
    "pricing_model": "tiered",
    "tier1_rate": "3.025",
    "tier2_rate": "3.865",
    "tier1_limit_kwh": "116.00",
    "flat_rate_kwh": null,
    "vat_rate": "0.1500",
    "vending_fee": "10.00",
    "receipt_dir_template": "/path/to/receipts",
    "created_at": "2024-12-27T10:00:00Z",
    "updated_at": "2024-12-27T10:00:00Z",
    "meter_count": 2
  }
]
```

**Status Codes**:
- `200`: Success
- `401`: Unauthorized
- `500`: Server error

---

### GET /api/properties/{property_config_key}/meters
**Purpose**: Get detailed property information with all meters and transactions

**Headers**: `Authorization: Bearer <token>`

**Path Parameters**:
- `property_config_key`: Unique identifier for the property (e.g., "11_jansen_van_rensburg_street")

**Response**:
```json
{
  "id": 1,
  "name": "11 Jansen Van Rensburg Street",
  "config_key": "11_jansen_van_rensburg_street",
  "pricing_model": "tiered",
  "tier1_rate": "3.025",
  "tier2_rate": "3.865",
  "tier1_limit_kwh": "116.00",
  "vat_rate": "0.1500",
  "vending_fee": "10.00",
  "meters": [
    {
      "id": 1,
      "meter_number": "04240523540",
      "property_id": 1,
      "assigned_user_id": 1,
      "meter_type": "ELECTRICITY",
      "status": "Active",
      "config_user_name_hint": "Megan",
      "current_monthly_purchase_kwh": "150.25",
      "last_purchase_date": "2024-12-27T09:00:00Z",
      "last_token_sequence_month": "2024-12-01",
      "last_token_number_in_month": 5,
      "assigned_user": {
        "id": 1,
        "name": "Megan Smith",
        "email": "megan@example.com",
        "role": "Tenant"
      },
      "vending_transactions": [
        {
          "id": 1,
          "amount_paid_currency": "100.00",
          "kwh_vended": "25.450",
          "token_from_vendor": "DEMO_TOKEN_12345",
          "transaction_date": "2024-12-27T09:00:00Z",
          "receipt_reference": "VEND-1-20241227090000",
          "tariff_details_snapshot": {
            "property_name": "11 Jansen Van Rensburg Street",
            "pricing_model": "tiered",
            "vat_rate": "0.15"
          }
        }
      ]
    }
  ]
}
```

**Status Codes**:
- `200`: Success
- `404`: Property not found
- `401`: Unauthorized
- `500`: Server error

---

### POST /api/properties
**Purpose**: Create new property *(Not yet implemented)*

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "name": "Property Name",
  "config_key": "property_key",
  "address": "Property Address",
  "pricing_model": "flat",
  "flat_rate_kwh": "2.576",
  "vat_rate": "0.15",
  "vending_fee": "10.00"
}
```

---

### PUT /api/properties/{id}
**Purpose**: Update existing property *(Not yet implemented)*

---

### DELETE /api/properties/{id}
**Purpose**: Delete property *(Not yet implemented)*

## Token Generation

### POST /api/token/generate
**Purpose**: Generate electricity token for a specific meter

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "meter_number": "04240523540",
  "amount": "100.00"
}
```

**Response**:
```json
{
  "message": "Token generated successfully.",
  "meter_number": "04240523540",
  "amount_paid": "100.00",
  "kwh_vended": "25.450",
  "token": "DEMO_TOKEN_12345",
  "transaction_id": 1
}
```

**Status Codes**:
- `200`: Success
- `404`: Meter not found
- `400`: Invalid amount or inactive meter
- `401`: Unauthorized
- `500`: Token generation failed

## User Management *(Not yet implemented)*

### GET /api/users
**Purpose**: Get list of all users (Admin only)

### POST /api/users
**Purpose**: Create new user (Admin only)

### PUT /api/users/{id}
**Purpose**: Update user (Admin only)

### DELETE /api/users/{id}
**Purpose**: Delete user (Admin only)

## Meters *(Not yet implemented)*

### GET /api/meters
**Purpose**: Get all meters across all properties

### POST /api/meters
**Purpose**: Create new meter

### PUT /api/meters/{id}
**Purpose**: Update meter information

### DELETE /api/meters/{id}
**Purpose**: Delete meter

## Transactions

### GET /api/transactions
**Purpose**: Get transaction history *(Not yet implemented)*

### GET /api/transactions/{id}
**Purpose**: Get specific transaction details *(Not yet implemented)*

## Dashboard *(Not yet implemented)*

### GET /api/dashboard/stats
**Purpose**: Get system statistics

**Response**:
```json
{
  "total_properties": 3,
  "total_meters": 8,
  "total_users": 15,
  "monthly_revenue": "15750.00",
  "monthly_kwh_vended": "4250.00",
  "active_meters": 8,
  "recent_transactions": []
}
```

### GET /api/dashboard/health
**Purpose**: System health check

## Error Responses

All endpoints return errors in the following format:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Missing or invalid authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource doesn't exist
- `409`: Conflict - Resource already exists
- `422`: Validation Error - Invalid request data format
- `500`: Internal Server Error - Server-side error

## Rate Limiting

Currently no rate limiting is implemented, but recommended for production:
- Authentication endpoints: 5 requests per minute
- Token generation: 10 requests per minute per user
- General API: 100 requests per minute per user

## Data Models

### Property Pricing Models

**Flat Rate**:
- Single rate per kWh regardless of usage
- Fields: `flat_rate_kwh`, `vat_rate`, `vending_fee`

**Tiered Rate**:
- Different rates based on monthly usage tiers
- Fields: `tier1_rate`, `tier2_rate`, `tier1_limit_kwh`, `vat_rate`, `vending_fee`

### Meter Status Values
- `Active`: Meter is operational and can generate tokens
- `Inactive`: Meter temporarily disabled
- `Decommissioned`: Meter permanently removed

### User Roles
- `Tenant`: Can view assigned meters and purchase tokens
- `PropertyManager`: Can manage specific properties
- `Admin`: Full system access

## Integration Notes

### CyberVendIT Integration
- Token generation uses Playwright automation (no API available)
- Demo mode available via `CYBERVENDIT_DEMO_MODE=true`
- Real tokens require valid CyberVendIT credentials

### PDF Receipts
- Generated automatically for each transaction
- Saved to property-specific directories
- Include detailed pricing breakdowns and calculations

### Monthly Usage Reset
- kWh tracking resets automatically each month
- Supports tiered pricing calculations
- Maintains transaction history across resets