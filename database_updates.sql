-- These updates are not needed unless you have made database with older
-- versions of the software

-- Database update for syke021R
ALTER TABLE users CHANGE id uid INTEGER;
ALTER TABLE shifts CHANGE id sid INTEGER;

-- Database update for syke025F
ALTER TABLE persons ADD COLUMN end_date INTEGER DEFAULT NULL AFTER name;
ALTER TABLE persons ADD COLUMN start_date INTEGER DEFAULT NULL AFTER name;
ALTER TABLE persons ADD COLUMN comments VARCHAR(255) NULL AFTER computer_id;

-- Database update for syke029F
CREATE TABLE coaches (
  oid     INTEGER     NOT NULL AUTO_INCREMENT,
  name    VARCHAR(16) UNIQUE NOT NULL,
  INDEX USING BTREE(name(16)),
  PRIMARY KEY (oid)
) ENGINE = InnoDB CHARACTER SET utf8 COLLATE utf8_bin;

ALTER TABLE persons ADD COLUMN coach_id INTEGER DEFAULT NULL;
ALTER TABLE persons ADD CONSTRAINT FOREIGN KEY (coach_id) REFERENCES coaches(oid);

