-- Run this on your existing itcg_registration database
-- to add the declarant_email column that the new app.py requires

USE itcg_registration;

-- Add declarant_email column (after declarant_designation)
ALTER TABLE registrations
  ADD COLUMN `declarant_email` VARCHAR(255) DEFAULT NULL
  AFTER `declarant_designation`;
