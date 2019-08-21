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

-- Database update to correct user id auto increment
ALTER TABLE users MODIFY COLUMN uid INTEGER NOT NULL AUTO_INCREMENT;

-- Database update for syke036F
ALTER TABLE computers ADD COLUMN comments VARCHAR(255) NULL AFTER name;

-- Database update for syke038F
CREATE TABLE exceptions (
  eid         INTEGER  NOT NULL AUTO_INCREMENT,
  day         SMALLINT NOT NULL,
  person_id   INTEGER  NOT NULL,
  shift_id    INTEGER  NOT NULL,
  computer_id INTEGER  NOT NULL,
  FOREIGN KEY (person_id)   REFERENCES persons(pid),
  FOREIGN KEY (shift_id)    REFERENCES shifts(sid),
  FOREIGN KEY (computer_id) REFERENCES computers(cid),
  PRIMARY KEY (eid)
) ENGINE = InnoDB CHARACTER SET utf8 COLLATE utf8_bin;

