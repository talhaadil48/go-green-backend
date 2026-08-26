-- Migration: Add per-car signature support and per-car cancellation forms
-- Date: 2026-08-26
-- Description:
--   1. Add vehicle_reg column to cancellation_forms for per-car cancellation
--   2. Existing records with NULL vehicle_reg continue working as claim-level forms
--   3. New records can specify a vehicle_reg for per-car cancellation

-- ============================================================
-- 1. Add vehicle_reg to cancellation_forms
-- ============================================================
ALTER TABLE cancellation_forms
ADD COLUMN IF NOT EXISTS vehicle_reg VARCHAR(50);

-- Create an index for efficient per-car lookups
CREATE INDEX IF NOT EXISTS idx_cancellation_forms_vehicle_reg
ON cancellation_forms (claim_id, vehicle_reg)
WHERE vehicle_reg IS NOT NULL;

-- Add a unique constraint so there's only one cancellation form per car per claim
-- (but allow multiple NULL vehicle_reg entries for backward compatibility)
-- Note: PostgreSQL allows multiple NULLs in a unique constraint
CREATE UNIQUE INDEX IF NOT EXISTS uq_cancellation_form_per_car
ON cancellation_forms (claim_id, vehicle_reg)
WHERE vehicle_reg IS NOT NULL;

-- ============================================================
-- 2. Verify existing data is untouched
-- ============================================================
-- All existing cancellation_forms have vehicle_reg = NULL
-- This means they continue to work as claim-level forms
-- The frontend and backend code treats NULL vehicle_reg as "claim-level"
