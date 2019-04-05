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

-- Database update for syke031B
ALTER TABLE coaches MODIFY name VARCHAR(64);

-- Database update for syke030F
LOCK TABLES shifts WRITE, persons WRITE;
-- Name of the foreing key rule may be different
ALTER TABLE persons DROP FOREIGN KEY persons_ibfk_1;
ALTER TABLE shifts MODIFY COLUMN sid INTEGER NOT NULL AUTO_INCREMENT;
ALTER TABLE persons ADD CONSTRAINT persons_ibfk_1 FOREIGN KEY (shift_id) REFERENCES shifts (sid);
UNLOCK TABLES;

