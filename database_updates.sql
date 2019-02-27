-- These updates are not needed unless you have made database with older
-- versions of the software

-- Database update for syke021R
ALTER TABLE users CHANGE id uid INTEGER;
ALTER TABLE shifts CHANGE id sid INTEGER;

-- Database update for syke025F
ALTER TABLE persons ADD COLUMN end_date INTEGER DEFAULT NULL AFTER name;
ALTER TABLE persons ADD COLUMN start_date INTEGER DEFAULT NULL AFTER name;
ALTER TABLE persons ADD COLUMN comments VARCHAR(255) NULL AFTER computer_id;

