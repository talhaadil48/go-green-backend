# Go Green — Full API Documentation

> **Base URL:** `http://localhost:8000`  
> **Format:** All requests and responses use `Content-Type: application/json`  
> **Authentication:** Every route under `/api/…` requires a Bearer JWT in the header:
>
> ```
> Authorization: Bearer <access_token>
> ```
>
> Routes under `/post/…` and `/auth/…` do **not** require authentication.

---

## Table of Contents

1. [Authentication (`/auth`)](#auth-routes)
2. [Form Data Upserts (`/post`)](#post-routes)
3. [API — Forms & Accident Claims (`/api`)](#api-forms)
4. [API — Claims CRUD & Lifecycle (`/api`)](#api-claims)
5. [API — Claim Documents (`/api`)](#api-documents)
6. [API — Users & Auth Management (`/api`)](#api-users)
7. [API — Cars (`/api`)](#api-cars)
8. [API — Invoices (`/api`)](#api-invoices)
9. [API — Long-Hire (`/api`)](#api-long-hire)
10. [Quick-Start Smoke Test](#quick-start)

---

## Auth Routes

### `POST /auth/login`

Log in and receive access + refresh tokens.

**Query parameters:**

| Parameter  | Type   | Required | Description       |
|------------|--------|----------|-------------------|
| `username` | string | ✅       | Account username  |
| `password` | string | ✅       | Account password  |

**Success response (200):**

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "role": "admin",
    "permissions": {}
  }
}
```

**Error responses:**

| Status | Detail                          |
|--------|---------------------------------|
| 400    | `"Invalid username or password"` |

---

### `POST /auth/refresh`

Exchange a valid refresh token for a new access + refresh token pair.

**Query parameters:**

| Parameter       | Type   | Required | Description          |
|-----------------|--------|----------|----------------------|
| `refresh_token` | string | ✅       | The current JWT refresh token |

**Success response (200):**

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Error responses:**

| Status | Detail                            |
|--------|-----------------------------------|
| 401    | `"Invalid or expired refresh token"` |
| 401    | `"Invalid token type"`             |
| 401    | `"Invalid token payload"`          |

---

## Post Routes

> **Prefix:** `/post`  
> **Auth:** None required

### `POST /post/accident-claims/{claim_id}`  
### `PUT /post/accident-claims/{claim_id}`

Create or update an accident claim form.  
Both `POST` and `PUT` behave identically (upsert).

> ⚠️ **Note:** `claim_id` is read from the request **body**, not the path. The path parameter is ignored.

**Request body (all fields optional — send only what you want to save):**

| Field                     | Type     | Description                             |
|---------------------------|----------|-----------------------------------------|
| `claim_id`                | string   | ID of the claim (required in body)      |
| `checklist_vd`            | boolean  | V.D checklist                           |
| `checklist_pi`            | boolean  | PI checklist                            |
| `checklist_dvla`          | boolean  | DVLA checklist                          |
| `checklist_badge`         | boolean  | Badge checklist                         |
| `checklist_recovery`      | boolean  | Recovery checklist                      |
| `checklist_hire`          | boolean  | Hire checklist                          |
| `checklist_ni_no`         | boolean  | NI Number checklist                     |
| `checklist_storage`       | boolean  | Storage checklist                       |
| `checklist_plate`         | boolean  | Plate checklist                         |
| `checklist_licence`       | boolean  | Licence checklist                       |
| `checklist_logbook`       | boolean  | Logbook checklist                       |
| `date_of_claim`           | string   | Date claim was opened                   |
| `accident_date`           | string   | Date of accident                        |
| `accident_time`           | string   | Time of accident                        |
| `accident_location`       | string   | Location of accident                    |
| `accident_description`    | string   | Description of what happened            |
| `owner_full_name`         | string   | Vehicle owner's full name               |
| `owner_email`             | string   |                                         |
| `owner_telephone`         | string   |                                         |
| `owner_address`           | string   |                                         |
| `owner_postcode`          | string   |                                         |
| `owner_dob`               | string   | Date of birth                           |
| `owner_ni_number`         | string   | National Insurance number               |
| `owner_occupation`        | string   |                                         |
| `driver_*`                | string   | Same fields as owner, for the driver    |
| `client_vehicle_make`     | string   |                                         |
| `client_vehicle_model`    | string   |                                         |
| `client_registration`     | string   |                                         |
| `client_policy_no`        | string   |                                         |
| `client_cover_type`       | string   |                                         |
| `client_policy_holder`    | string   |                                         |
| `third_party_*`           | string   | Third-party name, address, vehicle etc. |
| `fault_opinion`           | string   |                                         |
| `fault_reason`            | string   |                                         |
| `road_conditions`         | string   |                                         |
| `weather_conditions`      | string   |                                         |
| `witness1_name`           | string   |                                         |
| `witness1_address`        | string   |                                         |
| `witness1_postcode`       | string   |                                         |
| `witness1_telephone`      | string   |                                         |
| `witness2_*`              | string   | Same as witness1                        |
| `loss_of_earnings`        | boolean  |                                         |
| `employer_details`        | string   |                                         |
| `print_name`              | string   |                                         |
| `declaration_date`        | string   |                                         |
| `client_signature`        | string   | Base64 image or URL                     |
| `circumstance_drawing`    | string   | Base64 image or URL                     |
| `direction_before_drawing`| string   |                                         |
| `direction_after_drawing` | string   |                                         |

**Success response (200):** Full accident claim object (same fields as above).

**Error responses:**

| Status | Detail                   |
|--------|--------------------------|
| 400    | `"Invalid JSON"`         |
| 500    | `"Failed to save claim"` |

---

### `POST /post/pre-inspection-forms`

Create a new pre-inspection form, or update an existing one.

**Request body:**

| Field            | Type    | Required | Description                                         |
|------------------|---------|----------|-----------------------------------------------------|
| `claim_id`       | string  | ✅       | Parent claim ID                                     |
| `inspection_id`  | string  | ❌       | Omit to create new; provide to update existing row  |
| `condition_1`–`condition_30` | string | ❌ | Vehicle condition checkpoints             |
| `date`           | string  | ❌       |                                                     |
| `customer`       | string  | ❌       | Customer name                                       |
| `detailer`       | string  | ❌       |                                                     |
| `order_number`   | string  | ❌       |                                                     |
| `year`           | string  | ❌       | Vehicle year                                        |
| `make`           | string  | ❌       | Vehicle make                                        |
| `model`          | string  | ❌       | Vehicle model                                       |
| `notes`          | string  | ❌       |                                                     |
| `recommendations`| string  | ❌       |                                                     |
| `customer_signature`  | string | ❌  | Base64 image or URL                                 |
| `detailer_signature`  | string | ❌  |                                                     |
| `base_vehicle_image`  | string | ❌  |                                                     |
| `annotated_vehicle_image` | string | ❌ |                                                  |

**Success response (200):** Saved pre-inspection form row with all fields plus `inspection_id`.

**Error responses:**

| Status | Detail                                    |
|--------|-------------------------------------------|
| 400    | `"claim_id is required..."`               |
| 500    | `"Failed to save pre-inspection form"`    |

---

### `POST /post/cancellation-forms`

Create or update a cancellation form.

**Request body:**

| Field                   | Type   | Required | Description                       |
|-------------------------|--------|----------|-----------------------------------|
| `claim_id`              | string | ✅       |                                   |
| `name`                  | string | ❌       |                                   |
| `address`               | string | ❌       |                                   |
| `postcode`              | string | ❌       |                                   |
| `email`                 | string | ❌       |                                   |
| `cancellation_date`     | string | ❌       |                                   |
| `cancellation_signature`| string | ❌       | Base64 image or URL               |

**Success response (200):**

```json
{
  "name": "Jane Smith",
  "address": "123 Main St",
  "postcode": "AB1 2CD",
  "email": "jane@example.com",
  "cancellation_date": "2024-01-15",
  "cancellation_signature": "data:image/png;base64,...",
  "claim_id": "CLM-001"
}
```

**Error responses:**

| Status | Detail                                   |
|--------|------------------------------------------|
| 400    | `"claim_id is required..."`              |
| 500    | `"Failed to save cancellation form"`     |

---

### `POST /post/storage-forms`

Create or update a storage form / storage invoice.

**Request body:**

| Field                   | Type   | Required | Description              |
|-------------------------|--------|----------|--------------------------|
| `claim_id`              | string | ✅       |                          |
| `name`                  | string | ❌       | Client name              |
| `postcode`              | string | ❌       |                          |
| `address1`              | string | ❌       |                          |
| `address2`              | string | ❌       |                          |
| `vehicle_make`          | string | ❌       |                          |
| `vehicle_model`         | string | ❌       |                          |
| `registration_number`   | string | ❌       |                          |
| `date_of_recovery`      | string | ❌       |                          |
| `storage_start_date`    | string | ❌       |                          |
| `storage_end_date`      | string | ❌       |                          |
| `number_of_days`        | number | ❌       |                          |
| `charges_per_day`       | number | ❌       |                          |
| `total_storage_charge`  | number | ❌       |                          |
| `recovery_charge`       | number | ❌       |                          |
| `subtotal`              | number | ❌       |                          |
| `vat_amount`            | number | ❌       |                          |
| `invoice_total`         | number | ❌       |                          |
| `client_date`           | string | ❌       |                          |
| `owner_date`            | string | ❌       |                          |
| `client_signature`      | string | ❌       | Base64 image or URL      |
| `owner_signature`       | string | ❌       | Base64 image or URL      |

**Success response (200):** Saved storage form row with all fields.

**Error responses:**

| Status | Detail                              |
|--------|-------------------------------------|
| 400    | `"claim_id is required..."`         |
| 500    | `"Failed to save storage form"`     |

---

### `POST /post/rental-agreements`

Create or update a rental agreement.

**Request body:**  
`claim_id` is **required**. All other fields are optional (partial update supported).

Key fields:

| Field                      | Type   | Description                             |
|----------------------------|--------|-----------------------------------------|
| `claim_id`                 | string | **Required**                            |
| `hirer_name`               | string |                                         |
| `title`                    | string |                                         |
| `permanent_address`        | string |                                         |
| `licence_no`               | string |                                         |
| `date_issued`              | string |                                         |
| `expiry_date`              | string |                                         |
| `dob`                      | string |                                         |
| `occupation`               | string |                                         |
| `daily_rate`               | number |                                         |
| `policy_excess`            | number |                                         |
| `deposit`                  | number |                                         |
| `hire_vehicle_reg`         | string | Vehicle provided to hirer               |
| `hire_vehicle_date_out`    | string | Date vehicle was given out              |
| `hire_vehicle_date_in`     | string | Date vehicle was returned               |
| `total_days`               | number | Calculated number of days               |
| `rate_per_day`             | number |                                         |
| `total_cost`               | number | Final total including all charges       |
| `hirer_signature_terms`    | string | Base64 image or URL                     |
| `declaration_signature`    | string |                                         |

> When `hire_vehicle_date_out` is set, the parent claim status is updated to `"hire start"`.  
> When both `hire_vehicle_date_out` and `hire_vehicle_date_in` are set, status becomes `"hire end"`.

**Success response (200):** Full rental agreement row.

---

### `PUT /post/claim-documents/{claim_id}`

Upload or merge documents into a claim's document map.

**Path parameters:**

| Parameter  | Type   | Description    |
|------------|--------|----------------|
| `claim_id` | string | Claim ID       |

**Request body:**

```json
{
  "documents": {
    "driving_licence": "https://...",
    "insurance_cert": "data:image/png;base64,..."
  }
}
```

**Success response (200):**

```json
{
  "message": "Documents saved successfully",
  "claim_id": "CLM-001",
  "documents": { "driving_licence": "..." }
}
```

---

### `GET /post/claim-documents/{claim_id}`

Retrieve all documents for a claim.

**Success response (200):**

```json
{
  "claim_id": "CLM-001",
  "documents": {
    "driving_licence": "https://...",
    "insurance_cert": "https://..."
  }
}
```

**Error responses:**

| Status | Detail                    |
|--------|---------------------------|
| 404    | `"Documents not found"`   |

---

### `GET /post/recently`

Permanently deletes any soft-deleted claims older than 3 days.

**Success response (200):**

```json
{
  "success": true,
  "deleted_count": 3
}
```

---

### `POST /post/hire-checklists`

Create or update a hire checklist (vehicle inspection checklist for long-hire).

**Request body:**

| Field           | Type    | Required | Description                                          |
|-----------------|---------|----------|------------------------------------------------------|
| `long_claim_id` | string  | ✅       |                                                      |
| `car_id`        | integer | ✅       |                                                      |
| `claimant_id`   | integer | ✅       |                                                      |
| `condition_1`–`condition_30` | string | ❌ | Vehicle condition items              |
| `date`          | string  | ❌       |                                                      |
| `customer`      | string  | ❌       |                                                      |
| `detailer`      | string  | ❌       |                                                      |
| `order_number`  | string  | ❌       |                                                      |
| `year`          | string  | ❌       |                                                      |
| `make`          | string  | ❌       |                                                      |
| `model`         | string  | ❌       |                                                      |
| `notes`         | string  | ❌       |                                                      |
| `recommendations` | string | ❌     |                                                      |
| `customer_signature` | string | ❌  |                                                      |
| `detailer_signature` | string | ❌  |                                                      |
| `base_vehicle_image` | string | ❌  |                                                      |
| `annotated_vehicle_image` | string | ❌ |                                                 |

**Success response (200):** Saved checklist row with `inspection_id` included.

---

## API Forms

> **Prefix:** `/api`  
> **Auth:** Bearer JWT required for all routes in this section

### `GET /api/accident-claims/{claim_id}`

Retrieve the full accident claim form for a claim.

**Path parameters:**

| Parameter  | Type   | Description |
|------------|--------|-------------|
| `claim_id` | string | Claim ID    |

**Success response (200):** Full accident claim object (same fields documented under `POST /post/accident-claims`).

**Error responses:**

| Status | Detail                          |
|--------|---------------------------------|
| 404    | `"Accident claim not found"`    |

---

### `PUT /api/accident-claims/{claim_id}/direction`

Update the before/after direction drawing (and optional JSON canvas data) on an accident claim.

**Request body:**

| Field       | Type   | Required | Description                               |
|-------------|--------|----------|-------------------------------------------|
| `type`      | string | ✅       | `"before"` or `"after"`                  |
| `value`     | string | ✅       | Drawing URL or base64 string              |
| `json_data` | object | ❌       | Canvas JSON from drawing tool             |

**Success response (200):**

```json
{
  "claim_id": "CLM-001",
  "updated_value_column": "direction_before_drawing",
  "value": "data:image/png;base64,..."
}
```

**Error responses:**

| Status | Detail                              |
|--------|-------------------------------------|
| 400    | `"type must be 'before' or 'after'"` |
| 400    | `"value is required"`               |

---

### `GET /api/pre-inspection-forms/{claim_id}`

Return all pre-inspection forms associated with a claim (may be multiple).

**Success response (200):** Array of pre-inspection form objects.

---

### `GET /api/pre-inspection-forms/inspection/{inspection_id}`

Return a single pre-inspection form by its unique inspection ID.

**Error responses:**

| Status | Detail                                                    |
|--------|-----------------------------------------------------------|
| 404    | `"Pre-inspection form not found for this inspection_id"` |

---

### `GET /api/cancellation-forms/{claim_id}`

Return the cancellation form for a claim.

**Error responses:**

| Status | Detail                          |
|--------|---------------------------------|
| 404    | `"Cancellation form not found"` |

---

### `GET /api/storage-forms/{claim_id}`

Return the storage form for a claim.

**Error responses:**

| Status | Detail                      |
|--------|-----------------------------|
| 404    | `"Storage form not found"`  |

---

### `GET /api/rental-agreements/{claim_id}`

Return the rental agreement for a claim.

**Error responses:**

| Status | Detail                           |
|--------|----------------------------------|
| 404    | `"Rental agreement not found"`   |

---

## API Claims

### `POST /api/claims`

Create a new short claim.

**Request body:**

| Field            | Type   | Required | Description                      |
|------------------|--------|----------|----------------------------------|
| `claimant_name`  | string | ✅       |                                  |
| `claim_type`     | string | ✅       | e.g. `"accident"`, `"storage"`   |
| `council`        | string | ❌       | Council name if applicable       |
| `claim_id`       | string | ❌       | Custom ID; auto-generated if omitted |

**Success response (200):**

```json
{
  "message": "Claim created successfully",
  "claim_id": "CLM-001"
}
```

**Error responses:**

| Status | Detail                              |
|--------|-------------------------------------|
| 400    | `"claimant_name, claim_type and council are required"` |
| 409    | `"claim_id already exists"`         |

---

### `DELETE /api/claims/{claim_id}`

Permanently delete a claim.

**Success response (200):**

```json
{
  "message": "Claim deleted successfully",
  "claim_id": "CLM-001"
}
```

**Error responses:**

| Status | Detail                |
|--------|-----------------------|
| 404    | `"Claim not found"`   |

---

### `GET /api/claims`

Return all active (non-soft-deleted) claims with their latest invoice summary.

**Success response (200):** Array of claim objects, each including:

- `claim_id`, `claimant_name`, `claim_type`, `council`, `status`
- `recently_deleted` (bool), `closed_by`, `closed_date`
- `invoice_id`, `invoice_datetime`, `info` (from latest invoice, if exists)

---

### `GET /api/claims/{claim_id}`

Return a single claim by its ID.

**Error responses:**

| Status | Detail              |
|--------|---------------------|
| 404    | `"Claim not found"` |

---

### `PUT /api/claims/{claim_id}`

Update the claimant name on a claim.

**Request body:**

| Field           | Type   | Required | Description     |
|-----------------|--------|----------|-----------------|
| `claimant_name` | string | ✅       | New name        |

**Success response (200):**

```json
{
  "message": "Claimant name updated successfully",
  "claim_id": "CLM-001"
}
```

---

### `PUT /api/claims/{claim_id}/soft-delete`

Soft-delete a claim (it will appear in "recently deleted" list but is not removed from the database).

**Request body:**

| Field        | Type   | Required | Description                      |
|--------------|--------|----------|----------------------------------|
| `deleted_by` | string | ✅       | Username of the person deleting  |

**Success response (200):**

```json
{
  "message": "Claim soft deleted successfully",
  "claim_id": "CLM-001",
  "deleted_by": "admin"
}
```

---

### `PUT /api/claims/{claim_id}/close`

Close a claim.

**Request body:**

| Field       | Type   | Required | Description                      |
|-------------|--------|----------|----------------------------------|
| `closed_by` | string | ✅       | Username of the person closing   |

**Success response (200):**

```json
{
  "message": "Claim closed successfully",
  "claim_id": "CLM-001",
  "closed_by": "admin"
}
```

---

### `PUT /api/claims/{claim_id}/reopen`

Reopen a previously closed claim.

**Success response (200):**

```json
{
  "message": "Claim reopened successfully",
  "claim_id": "CLM-001"
}
```

---

### `PUT /api/claims/{claim_id}/restore`

Restore a soft-deleted short claim.

**Success response (200):**

```json
{
  "message": "Claim restored successfully",
  "claim_id": "CLM-001"
}
```

---

### `PUT /api/claims/{claim_id}/status`

Manually set the status field of a claim.

**Request body:**

| Field    | Type   | Required | Description             |
|----------|--------|----------|-------------------------|
| `status` | string | ✅       | New status value        |

**Success response (200):**

```json
{
  "message": "Status updated successfully",
  "claim_id": "CLM-001",
  "status": "hire start"
}
```

---

### `GET /api/recently`

Return all soft-deleted (recently deleted) claims.

**Success response (200):**

```json
{
  "count": 2,
  "claims": [
    {
      "claim_id": "CLM-001",
      "claimant_name": "John Smith",
      "recently_deleted_date": "2024-01-10T09:00:00",
      "deleted_by": "admin"
    }
  ]
}
```

---

### `GET /api/claim-bill/{claim_id}`

Return the rental and storage totals for a short claim (billing summary).

**Success response (200):**

```json
{
  "rental": 450.00,
  "storage": 120.00
}
```

> Either value may be `null` if no rental agreement / storage form exists.

---

## API Documents

### `PUT /api/claim-documents/{claim_id}`

Create or merge documents into a claim's document map (JSON object key-value store).

**Request body:**

```json
{
  "documents": {
    "driving_licence": "https://...",
    "insurance_cert": "data:image/png;base64,..."
  }
}
```

**Success response (200):**

```json
{
  "message": "Documents saved successfully",
  "claim_id": "CLM-001",
  "documents": { "driving_licence": "..." }
}
```

---

### `GET /api/claim-documents/{claim_id}`

Return all saved documents for a claim.

**Success response (200):**

```json
{
  "claim_id": "CLM-001",
  "documents": {
    "driving_licence": "https://...",
    "insurance_cert": "https://..."
  }
}
```

**Error responses:**

| Status | Detail                  |
|--------|-------------------------|
| 404    | `"Documents not found"` |

---

### `DELETE /api/claim-documents/{claim_id}/{doc_name}`

Remove a specific document by name from a claim's document map.

**Path parameters:**

| Parameter  | Type   | Description          |
|------------|--------|----------------------|
| `claim_id` | string |                      |
| `doc_name` | string | Key name to remove   |

**Success response (200):**

```json
{
  "message": "Document 'driving_licence' deleted successfully",
  "claim_id": "CLM-001"
}
```

**Error responses:**

| Status | Detail                                        |
|--------|-----------------------------------------------|
| 404    | `"Document not found for this claim"`         |

---

## API Users

> All user management routes require the authenticated user to have `role = "admin"`.

### `POST /api/register`

Create a new user account.

**Request body:**

| Field      | Type   | Required | Description                          |
|------------|--------|----------|--------------------------------------|
| `username` | string | ✅       |                                      |
| `password` | string | ✅       | Plain-text; hashed before storage    |
| `role`     | string | ✅       | e.g. `"user"`, `"admin"`             |

**Success response (200):**

```json
{
  "message": "User created successfully"
}
```

**Error responses:**

| Status | Detail                          |
|--------|---------------------------------|
| 400    | `"User already exists"`         |
| 403    | `"Admin privileges required"`   |

---

### `PUT /api/change-password`

Change another user's password.

**Request body:**

| Field          | Type   | Required | Description       |
|----------------|--------|----------|-------------------|
| `username`     | string | ✅       |                   |
| `new_password` | string | ✅       |                   |

**Success response (200):**

```json
{
  "message": "Password updated successfully"
}
```

**Error responses:**

| Status | Detail                        |
|--------|-------------------------------|
| 403    | `"Admin privileges required"` |
| 404    | `"User not found"`            |

---

### `DELETE /api/users/{user_id}`

Delete a user account.

**Path parameters:**

| Parameter | Type    | Description |
|-----------|---------|-------------|
| `user_id` | integer |             |

**Success response (200):**

```json
{
  "message": "User deleted successfully"
}
```

**Error responses:**

| Status | Detail                        |
|--------|-------------------------------|
| 403    | `"Admin privileges required"` |
| 404    | `"User not found"`            |

---

### `GET /api/users`

Return all non-admin user accounts.

**Success response (200):**

```json
{
  "users": [
    { "id": 2, "username": "jane_doe", "role": "user" }
  ]
}
```

---

## API Cars

### `POST /api/car`

Add a new car to the fleet.

**Request body:**

| Field    | Type   | Required | Description             |
|----------|--------|----------|-------------------------|
| `model`  | string | ✅       | e.g. `"Corsa"`          |
| `name`   | string | ✅       | Display name / nickname |
| `reg_no` | string | ✅       | Registration number     |

**Success response (200):**

```json
{
  "success": true,
  "message": "Car created successfully"
}
```

---

### `PUT /api/car/{car_id}`

Update a car's details.

**Request body:** Same as `POST /api/car`.

**Success response (200):**

```json
{
  "success": true,
  "message": "Car updated successfully"
}
```

**Error responses:**

| Status | Detail              |
|--------|---------------------|
| 404    | `"Car not found"`   |

---

### `DELETE /api/car/{car_id}`

Permanently remove a car from the fleet.

**Success response (200):**

```json
{
  "success": true,
  "message": "Car deleted successfully"
}
```

---

### `GET /api/car/{car_id}`

Return a single car by ID.

**Success response (200):**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "model": "Corsa",
    "name": "Go Green 1",
    "reg_no": "AB12 CDE"
  }
}
```

**Error responses:**

| Status | Detail             |
|--------|--------------------|
| 404    | `"Car not found"`  |

---

### `GET /api/cars`

Return all cars in the fleet.

**Success response (200):**

```json
{
  "success": true,
  "count": 5,
  "data": [ { "id": 1, "model": "Corsa", "name": "Go Green 1", "reg_no": "AB12 CDE" } ]
}
```

---

### `GET /api/cars/available`

Return cars that are **not** currently on hire (no active claimant with a missing `end_date`).

**Success response (200):** Same shape as `GET /api/cars`.

---

## API Invoices

### `POST /api/invoice`

Create a short-claim invoice.

**Request body:**

| Field          | Type   | Required | Description                         |
|----------------|--------|----------|-------------------------------------|
| `claim_id`     | string | ✅       |                                     |
| `info`         | string | ❌       | Free-text notes                     |
| `docs`         | array  | ❌       | List of document references         |
| `storage_bill` | number | ❌       | Storage charge amount               |
| `rent_bill`    | number | ❌       | Rental charge amount                |
| `user_name`    | string | ❌       | Name of user creating the invoice   |

**Success response (200):**

```json
{
  "success": true,
  "invoice_id": 42
}
```

---

### `PUT /api/invoice/{invoice_id}`

Update an existing short-claim invoice (partial update).

**Request body:** Any subset of `info`, `storage_bill`, `rent_bill`, `user_name`.

**Success response (200):**

```json
{
  "success": true,
  "invoice_id": 42
}
```

---

### `GET /api/invoice`

Return all short-claim invoices (all claims), newest first.

**Success response (200):**

```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "id": 42, "claim_id": "CLM-001", "claimant_name": "John Smith",
      "invoice_datetime": "2024-01-10T12:00:00",
      "info": "...", "docs": [], "storage_bill": 120.0,
      "rent_bill": 450.0, "user_name": "admin"
    }
  ]
}
```

---

### `GET /api/invoice/{claim_id}`

Return all invoices for a specific claim.

**Success response (200):** Same shape as `GET /api/invoice`.

---

### `POST /api/long_hire_invoice`

Create a long-hire invoice and automatically mark the parent long-claim as invoiced.

**Request body:**

| Field       | Type   | Required | Description                  |
|-------------|--------|----------|------------------------------|
| `claim_id`  | string | ✅       | Long-hire claim ID           |
| `amount`    | number | ✅       | Total invoice amount         |
| `user_name` | string | ✅       | Name of user creating it     |

**Success response (200):**

```json
{
  "success": true,
  "invoice_id": 7
}
```

---

### `GET /api/long_hire_invoice`

Return all long-hire invoices, newest first.

**Success response (200):**

```json
{
  "success": true,
  "count": 3,
  "data": [
    {
      "id": 7, "claim_id": "LHC-001", "hirer_name": "ACME Ltd",
      "amount": 1500.00, "date_sent": "2024-01-15", "user_name": "admin"
    }
  ]
}
```

---

## API Long-Hire

### `POST /api/long-claim`

Create a new long-hire claim.

**Request body:**

| Field           | Type   | Required | Description         |
|-----------------|--------|----------|---------------------|
| `starting_date` | string | ❌       | ISO date string     |
| `ending_date`   | string | ❌       |                     |
| `hirer_name`    | string | ❌       |                     |

**Success response (200):**

```json
{
  "success": true,
  "long_claim_id": "LHC-001"
}
```

---

### `PUT /api/long-claim`

Update a long-hire claim.

**Request body:**

| Field            | Type   | Required | Description          |
|------------------|--------|----------|----------------------|
| `long_claim_id`  | string | ✅       |                      |
| `starting_date`  | string | ❌       |                      |
| `ending_date`    | string | ❌       |                      |
| `hirer_name`     | string | ❌       |                      |

**Success response (200):**

```json
{
  "success": true,
  "message": "Long claim updated successfully"
}
```

---

### `GET /api/long-claims`

Return all active (non-soft-deleted) long-hire claims.

**Success response (200):**

```json
{
  "success": true,
  "count": 4,
  "data": [
    {
      "id": "LHC-001", "starting_date": "2024-01-01", "ending_date": "2024-03-31",
      "invoice_sent": false, "date_sent": null, "hirer_name": "ACME Ltd"
    }
  ]
}
```

---

### `GET /api/long-claims/{claim_id}`

Return a single long-hire claim.

**Success response (200):**

```json
{
  "success": true,
  "data": {
    "id": "LHC-001", "starting_date": "2024-01-01",
    "ending_date": "2024-03-31", "invoice_sent": false, "hirer_name": "ACME Ltd"
  }
}
```

---

### `PUT /api/long-claims/{claim_id}/restore`

Restore a soft-deleted long-hire claim.

**Success response (200):**

```json
{
  "success": true,
  "message": "Claim LHC-001 restored successfully."
}
```

---

### `DELETE /api/long-claims/{claim_id}/delete`

Permanently delete a long-hire claim.

**Success response (200):**

```json
{
  "success": true,
  "message": "Claim LHC-001 deleted permanently."
}
```

---

### `PATCH /api/long-claims/{claim_id}/mark-deleted`

Soft-delete a long-hire claim.

**Request body:**

| Field        | Type   | Required | Description                      |
|--------------|--------|----------|----------------------------------|
| `deleted_by` | string | ✅       | Username of person deleting      |

**Success response (200):**

```json
{
  "success": true,
  "message": "Claim LHC-001 marked as recently deleted by admin."
}
```

---

### `GET /api/long/soft-deleted`

Return all soft-deleted long-hire claims.

**Success response (200):**

```json
{
  "success": true,
  "count": 1,
  "data": [
    {
      "id": "LHC-002", "hirer_name": "Beta Ltd",
      "deleted_by": "admin", "recently_deleted_date": "..."
    }
  ]
}
```

---

### `POST /api/long-claim/{long_claim_id}/add-car`

Assign a car to a long-hire claim.

**Request body:**

| Field    | Type    | Required |
|----------|---------|----------|
| `car_id` | integer | ✅       |

**Success response (200):**

```json
{
  "success": true,
  "message": "Car added to long claim"
}
```

---

### `DELETE /api/long-claim/{long_claim_id}/remove-car/{car_id}`

Remove a car assignment from a long-hire claim.

**Success response (200):**

```json
{
  "success": true,
  "message": "Car removed from long claim"
}
```

---

### `GET /api/long-claim/{long_claim_id}/cars`

Return all cars currently assigned to a long-hire claim.

**Success response (200):**

```json
{
  "success": true,
  "count": 2,
  "data": [
    { "id": 1, "model": "Corsa", "name": "Go Green 1", "reg_no": "AB12 CDE" }
  ]
}
```

---

### `PUT /api/long-claim/{long_claim_id}/mark-invoice`

Mark a long-hire claim as invoiced (sets `invoice_sent = true`).

**Success response (200):**

```json
{
  "success": true,
  "message": "Invoice marked as true"
}
```

---

### `GET /api/long-claim/{long_claim_id}/daily-rates`

Return a map of `car_id → daily_rate` for all cars in the claim.

**Success response (200):**

```json
{
  "success": true,
  "data": {
    "1": 45.00,
    "3": 55.00
  }
}
```

---

### `PUT /api/long-claim/{long_claim_id}/daily-rate`

Update the daily rate for a specific car in a long-hire claim.

**Request body:**

| Field        | Type    | Required |
|--------------|---------|----------|
| `car_id`     | integer | ✅       |
| `daily_rate` | number  | ✅       |

**Success response (200):**

```json
{
  "success": true
}
```

---

### `POST /api/claimant`

Create a new claimant within a long-hire claim.

**Request body:**

| Field              | Type    | Required | Description                   |
|--------------------|---------|----------|-------------------------------|
| `long_claim_id`    | string  | ✅       |                               |
| `car_id`           | integer | ✅       |                               |
| `start_date`       | string  | ❌       |                               |
| `end_date`         | string  | ❌       | Set when hire ends            |
| `miles`            | number  | ❌       | Mileage at handover           |
| `name`             | string  | ❌       | Claimant name                 |
| `location`         | string  | ❌       | Pick-up/drop-off location     |
| `delivery_charges` | number  | ❌       | Default 0                     |

**Success response (200):**

```json
{
  "success": true,
  "claimant_id": 99
}
```

---

### `PUT /api/claimant/{claimant_id}`

Update claimant fields (partial update).

**Request body:** Any subset of `start_date`, `end_date`, `miles`, `name`, `location`, `delivery_charges`.

**Success response (200):**

```json
{
  "success": true,
  "message": "Claimant updated successfully"
}
```

---

### `DELETE /api/claimant/{claimant_id}`

Delete a claimant record.

**Success response (200):**

```json
{
  "success": true,
  "message": "Claimant deleted successfully"
}
```

---

### `GET /api/claimant/{claimant_id}`

Return claimant record(s) for a given ID.

**Success response (200):**

```json
{
  "success": true,
  "count": 1,
  "data": [
    { "id": 99, "long_claim_id": "LHC-001", "car_id": 1, "name": "Jane Smith" }
  ]
}
```

---

### `GET /api/claimants`

Return all claimant records across all claims.

**Success response (200):** Same shape as `GET /api/claimant/{claimant_id}`.

---

### `GET /api/car/{car_id}/claimants/{claim_id}`

Return all claimants for a specific car within a specific long-hire claim.

**Success response (200):**

```json
{
  "success": true,
  "count": 1,
  "data": [ { "id": 99, "name": "Jane Smith", ... } ]
}
```

---

### `GET /api/long-hire/{long_claim_id}/claimants`

Return all claimants for a long-hire claim, grouped by `car_id`.

**Success response (200):**

```json
{
  "success": true,
  "count": 3,
  "data": {
    "1": [ { "id": 99, "name": "Jane Smith", "start_date": "..." } ],
    "3": [ { "id": 100, "name": "Bob Jones", "start_date": "..." } ]
  }
}
```

---

### `GET /api/hire-checklists/{long_claim_id}/{car_id}/{claimant_id}`

Return all hire checklists for a specific (claim, car, claimant) combination.

**Success response (200):** Array of checklist objects, each including `inspection_id`, `long_claim_id`, `car_id`, `claimant_id`, all `condition_*` fields, and signature/image fields.

---

### `POST /api/hire-checklists` *(also available on `/post/hire-checklists`)*

Create or update a hire checklist. See [`POST /post/hire-checklists`](#post-hire-checklists) for field details.

---

## Quick-Start

### Running the app

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Swagger UI (interactive docs)

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI where you can try every endpoint.

### Smoke test (curl)

```bash
# 1. Log in and capture your access token
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login?username=admin&password=secret" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. List all claims
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/claims

# 3. Create a claim
curl -s -X POST http://localhost:8000/api/claims \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"claimant_name":"John Smith","claim_type":"accident","council":"Manchester"}'
```
