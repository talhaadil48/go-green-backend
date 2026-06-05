import asyncpg
import json
from app.db.base import record_to_dict, records_to_list


async def insert_claim(
    conn: asyncpg.Connection,
    claimant_name: str | None,
    claim_type: str | None,
    council: str | None,
    claim_id: str | None = None,
) -> bool:
    await conn.execute(
        "INSERT INTO claims (claim_id, claimant_name, claim_type, council) VALUES ($1, $2, $3, $4);",
        claim_id, claimant_name, claim_type, council,
    )
    return True


async def delete_claim(conn: asyncpg.Connection, claim_id: str) -> bool:
    result = await conn.execute("DELETE FROM claims WHERE claim_id = $1;", claim_id)
    return result != "DELETE 0"


async def get_all_claims(conn: asyncpg.Connection) -> list[dict]:
    query = """
        SELECT
            c.*,
            i.id AS invoice_id,
            i.invoice_datetime,
            i.info,
            CASE
                WHEN ra.hire_vehicle_date_in IS NOT NULL
                    AND EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                        WHERE NULLIF(j->>'date_out','') IS NOT NULL
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                        WHERE NULLIF(j->>'date_in','') IS NOT NULL
                    )
                THEN NULL
                ELSE GREATEST(
                    ra.hire_vehicle_date_in,
                    (
                        SELECT MAX((NULLIF(j->>'date_in',''))::date)
                        FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                        WHERE NULLIF(j->>'date_in','') IS NOT NULL
                    )
                )
            END AS hire_end_date,
            LEAST(
                ra.hire_vehicle_date_out,
                (
                    SELECT MIN((NULLIF(j->>'date_out',''))::date)
                    FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                    WHERE NULLIF(j->>'date_out','') IS NOT NULL
                )
            ) AS hire_start_date
        FROM claims c
        LEFT JOIN (
            SELECT DISTINCT ON (claim_id)
                id, claim_id, invoice_datetime, info
            FROM invoice
            ORDER BY claim_id, invoice_datetime DESC
        ) i ON c.claim_id = i.claim_id
        LEFT JOIN rental_agreements ra ON c.claim_id = ra.claim_id
        WHERE c.recently_deleted = FALSE;
    """
    rows = await conn.fetch(query)
    return records_to_list(rows)


async def get_claim_by_id(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM claims WHERE claim_id = $1;", claim_id)
    return record_to_dict(row)


async def update_claim_dynamic(conn: asyncpg.Connection, claim_id: str, update_data: dict) -> bool:
    if not update_data:
        return False
    fields = []
    values = []
    for i, (field, value) in enumerate(update_data.items(), start=1):
        fields.append(f"{field} = ${i}")
        values.append(value)
    values.append(claim_id)
    query = f"UPDATE claims SET {', '.join(fields)} WHERE claim_id = ${len(values)};"
    result = await conn.execute(query, *values)
    return result != "UPDATE 0"


async def soft_delete_claim(conn: asyncpg.Connection, claim_id: str, deleted_by: str) -> bool:
    result = await conn.execute(
        "UPDATE claims SET recently_deleted = TRUE, recently_deleted_date = NOW(), deleted_by = $1 WHERE claim_id = $2;",
        deleted_by, claim_id,
    )
    return result != "UPDATE 0"


async def restore_short_claim(conn: asyncpg.Connection, claim_id: str) -> bool:
    result = await conn.execute(
        "UPDATE claims SET recently_deleted = FALSE, recently_deleted_date = NOW(), deleted_by = NULL WHERE claim_id = $1;",
        claim_id,
    )
    return result != "UPDATE 0"


async def close_claim(conn: asyncpg.Connection, claim_id: str, closed_by: str, reason: str | None) -> bool:
    result = await conn.execute(
        "UPDATE claims SET closed_by = $1, closed_date = NOW(), reason = $2 WHERE claim_id = $3;",
        closed_by, reason, claim_id,
    )
    return result != "UPDATE 0"


async def reopen_claim(conn: asyncpg.Connection, claim_id: str) -> bool:
    result = await conn.execute(
        "UPDATE claims SET closed_by = NULL, closed_date = NULL, reason = NULL WHERE claim_id = $1;",
        claim_id,
    )
    return result != "UPDATE 0"


async def update_claim_status(conn: asyncpg.Connection, claim_id: str, status: str) -> bool:
    result = await conn.execute(
        "UPDATE claims SET status = $1 WHERE claim_id = $2;", status, claim_id
    )
    return result != "UPDATE 0"


async def update_claim_disputed(
    conn: asyncpg.Connection,
    claim_id: str,
    is_disputed=None,
    dispute_reason=None,
) -> bool:
    fields = []
    values = []
    if is_disputed is not None:
        fields.append(f"is_disputed = ${len(values)+1}")
        values.append(is_disputed)
    if dispute_reason is not None:
        fields.append(f"dispute_reason = ${len(values)+1}")
        values.append(dispute_reason)
    if not fields:
        return False
    values.append(claim_id)
    result = await conn.execute(
        f"UPDATE claims SET {', '.join(fields)} WHERE claim_id = ${len(values)};",
        *values,
    )
    return result != "UPDATE 0"


async def get_recently_deleted_claims(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch("SELECT * FROM claims WHERE recently_deleted = TRUE;")
    return records_to_list(rows)


async def permanently_delete_recently_deleted_claims(conn: asyncpg.Connection) -> int:
    result = await conn.execute(
        "DELETE FROM claims WHERE recently_deleted = TRUE AND recently_deleted_date < NOW() - INTERVAL '3 days';"
    )
    # result is like "DELETE 5"
    parts = result.split()
    return int(parts[1]) if len(parts) == 2 else 0


async def update_claim_lock(
    conn: asyncpg.Connection, claim_id: str, locked: bool, locked_by: str | None
) -> None:
    await conn.execute(
        "UPDATE claims SET locked = $1, locked_by = $2 WHERE claim_id = $3;",
        locked, locked_by, claim_id,
    )


async def get_claim_lock(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM claims WHERE claim_id = $1;", claim_id)
    return record_to_dict(row)


async def update_ref_no(conn: asyncpg.Connection, claim_id: str, ref_no: str) -> dict | None:
    row = await conn.fetchrow(
        "UPDATE claims SET ref_no = $1 WHERE claim_id = $2 RETURNING *;",
        ref_no, claim_id,
    )
    return record_to_dict(row)


async def update_payment_details(
    conn: asyncpg.Connection, claim_id: str, payment: str | None, pay_date: str | None
) -> dict | None:
    old = await conn.fetchrow(
        "SELECT payment, pay_date FROM claims WHERE claim_id = $1;", claim_id
    )
    if not old:
        return None

    fields = []
    values = []
    if payment is not None:
        fields.append(f"payment = ${len(values)+1}")
        values.append(payment)
    if pay_date is not None:
        fields.append(f"pay_date = ${len(values)+1}")
        values.append(pay_date)
    if not fields:
        return None

    values.append(claim_id)
    row = await conn.fetchrow(
        f"UPDATE claims SET {', '.join(fields)} WHERE claim_id = ${len(values)} RETURNING *;",
        *values,
    )
    result = record_to_dict(row)

    if result and old["pay_date"] is None and pay_date is not None:
        await update_claim_status(conn, claim_id, "client paid")

    return result


async def update_invoice_date(conn: asyncpg.Connection, claim_id: str, invoice_date) -> dict | None:
    row = await conn.fetchrow(
        "UPDATE claims SET invoice_date = $1 WHERE claim_id = $2 RETURNING *;",
        invoice_date, claim_id,
    )
    return record_to_dict(row)


async def add_update(conn: asyncpg.Connection, claim_id: str, new_update: dict) -> bool:
    import json as _json
    result = await conn.execute(
        "UPDATE claims SET updates = COALESCE(updates, '[]'::jsonb) || $1::jsonb WHERE claim_id = $2;",
        _json.dumps([new_update]), claim_id,
    )
    return result != "UPDATE 0"


async def edit_update(conn: asyncpg.Connection, claim_id: str, update_id: int, new_data: dict) -> bool:
    import json as _json
    row = await conn.fetchrow("SELECT updates FROM claims WHERE claim_id = $1;", claim_id)
    if not row or not row["updates"]:
        return False

    updates = row["updates"]
    if isinstance(updates, str):
        updates = _json.loads(updates)

    found = False
    for i, item in enumerate(updates):
        if item.get("id") == update_id:
            updates[i] = {**item, **new_data}
            found = True
            break

    if not found:
        return False

    await conn.execute(
        "UPDATE claims SET updates = $1 WHERE claim_id = $2;",
        _json.dumps(updates), claim_id,
    )
    return True


async def get_updates(conn: asyncpg.Connection, claim_id: str) -> list[dict]:
    row = await conn.fetchrow("SELECT updates FROM claims WHERE claim_id = $1;", claim_id)
    if not row or not row["updates"]:
        return []
    updates = row["updates"]
    if isinstance(updates, str):
        import json as _json
        return _json.loads(updates)
    return list(updates)


async def get_claim_summary(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    summary: dict = {
        "claim": None,
        "accident_claim": None,
        "rental_agreement": None,
        "storage_form": None,
        "invoices": [],
    }

    row = await conn.fetchrow(
        """SELECT claim_id, claimant_name, claim_type, claim_start_date, status,
                  closed_date, closed_by, recently_deleted, is_disputed, dispute_reason
           FROM claims WHERE claim_id = $1;""",
        claim_id,
    )
    if not row:
        return None
    summary["claim"] = record_to_dict(row)

    row = await conn.fetchrow(
        """SELECT checklist_vd,
                  driver_full_name, driver_email, driver_telephone, driver_address,
                  driver_postcode, driver_dob, driver_ni_number, driver_occupation,
                  client_vehicle_make, client_vehicle_model, client_registration,
                  client_policy_no, client_cover_type, client_policy_holder
           FROM accident_claims WHERE claim_id = $1;""",
        claim_id,
    )
    if row:
        summary["accident_claim"] = record_to_dict(row)

    row = await conn.fetchrow(
        """SELECT hire_vehicle_reg, hire_vehicle_make, hire_vehicle_model,
                  hire_vehicle_date_out, hire_vehicle_date_in,
                  hire_vehicle_miles_out, hire_vehicle_miles_in, change_vehicle_history
           FROM rental_agreements WHERE claim_id = $1;""",
        claim_id,
    )
    if row:
        summary["rental_agreement"] = record_to_dict(row)

    row = await conn.fetchrow(
        "SELECT storage_location_key FROM storage_forms WHERE claim_id = $1;",
        claim_id,
    )
    if row:
        summary["storage_form"] = {"storage_location_key": row["storage_location_key"]}

    rows = await conn.fetch(
        """SELECT id, invoice_datetime, info, storage_bill, rent_bill
           FROM invoice WHERE claim_id = $1 ORDER BY invoice_datetime DESC;""",
        claim_id,
    )
    summary["invoices"] = records_to_list(rows)

    return summary


async def get_claim_documents(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM claim_documents WHERE claim_id = $1;", claim_id)
    return record_to_dict(row)


async def upsert_claim_documents(conn: asyncpg.Connection, claim_id: str, documents: dict) -> None:
    import json as _json
    await conn.execute(
        """INSERT INTO claim_documents (claim_id, documents) VALUES ($1, $2)
           ON CONFLICT (claim_id)
           DO UPDATE SET documents = claim_documents.documents || EXCLUDED.documents;""",
        claim_id, _json.dumps(documents),
    )


async def delete_claim_document(conn: asyncpg.Connection, claim_id: str, doc_name: str) -> bool:
    row = await conn.fetchrow(
        "UPDATE claim_documents SET documents = documents - $1 WHERE claim_id = $2 RETURNING claim_id;",
        doc_name, claim_id,
    )
    return row is not None


async def update_hire_vehicle_dates(
    conn: asyncpg.Connection,
    claim_id: str,
    date_in: str | None = None,
    date_out: str | None = None,
) -> dict | None:
    row = await conn.fetchrow(
        """INSERT INTO rental_agreements (claim_id, hire_vehicle_date_in, hire_vehicle_date_out)
           VALUES ($1, $2, $3)
           ON CONFLICT (claim_id) DO UPDATE SET
               hire_vehicle_date_in = EXCLUDED.hire_vehicle_date_in,
               hire_vehicle_date_out = EXCLUDED.hire_vehicle_date_out
           RETURNING *;""",
        claim_id, date_in, date_out,
    )
    return record_to_dict(row)
