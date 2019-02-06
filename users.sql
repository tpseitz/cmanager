CREATE DATABASE IF NOT EXISTS computers
  CHARACTER SET utf8 COLLATE utf8_bin;
USE computers;

CREATE TABLE users (
  uid       INTEGER     NOT NULL AUTO_INCREMENT,
  created   DATETIME    DEFAULT NOW(),
  username  VARCHAR(16) UNIQUE NOT NULL,
  password  CHAR(106)   NOT NULL,
  fullname  VARCHAR(64) UNIQUE NOT NULL,
  level     INTEGER(1)  NOT NULL,
  lastpass  INTEGER(4)  DEFAULT NULL,
  lastlogin INTEGER(4)  DEFAULT NULL,
  tries     INTEGER(1)  DEFAULT 0,
  INDEX USING BTREE(username(16)),
  PRIMARY KEY (id)
) ENGINE = InnoDB CHARACTER SET utf8 COLLATE utf8_bin;

CREATE TABLE shifts (
  sid         INTEGER      NOT NULL AUTO_INCREMENT,
  ord         INTEGER(2)   UNIQUE NOT NULL,
  name        VARCHAR(16)  UNIQUE NOT NULL,
  max_users   INTEGER(2)   NOT NULL,
  description VARCHAR(256) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY (ord),
  INDEX USING BTREE(name(8))
) ENGINE = InnoDB CHARACTER SET utf8 COLLATE utf8_bin;

CREATE TABLE computers (
  cid     INTEGER     NOT NULL AUTO_INCREMENT,
  created DATETIME    DEFAULT NOW(),
  name    VARCHAR(16) UNIQUE NOT NULL,
  x       INTEGER     DEFAULT NULL,
  y       INTEGER     DEFAULT NULL,
  INDEX USING BTREE(name(16)),
  PRIMARY KEY (cid)
) ENGINE = InnoDB CHARACTER SET utf8 COLLATE utf8_bin;

CREATE TABLE persons (  
  pid         INTEGER     NOT NULL AUTO_INCREMENT,
  created     DATETIME    DEFAULT NOW(),
  name        VARCHAR(64) UNIQUE NOT NULL,
  shift_id    INTEGER     DEFAULT NULL,
  day_0       BOOLEAN     DEFAULT FALSE,
  day_1       BOOLEAN     DEFAULT FALSE,
  day_2       BOOLEAN     DEFAULT FALSE,
  day_3       BOOLEAN     DEFAULT FALSE,
  day_4       BOOLEAN     DEFAULT FALSE,
  computer_id INTEGER     DEFAULT NULL,
  FOREIGN KEY (shift_id) REFERENCES shifts(sid),
  FOREIGN KEY (computer_id) REFERENCES computers(cid),
  INDEX USING BTREE(name(64)),
  PRIMARY KEY (pid)
) ENGINE = InnoDB CHARACTER SET utf8 COLLATE utf8_bin;

INSERT INTO users (username, fullname, level, password)
  VALUES ("admin", "Temporary superuser", 250,
    "$6$xjUUbJX./EMVfyiU$NJ1Tt9zhIizzaU1lHffT8P4pxpZftmnoOzh9qYro8kBbePBbiz36cGvpxju.Sc3IHGmsc1lKWM244JaGL151D/");
INSERT INTO shifts (ord, name, max_users)
  VALUES (1, "morning",  20), (2, "day", 10);

-- Database update commands from older versions in syke021R
ALTER TABLE users CHANGE id uid INTEGER;
ALTER TABLE shifts CHANGE id sid INTEGER;

