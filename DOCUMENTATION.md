Computer and user management script documentation
=================================================

This document describes usage and configuration of the web application. Brand
of database used for it is MySQL (or MariaDB).

It is recommended to have scripts and data outside the public html directory
and linking or aliasing them to server. With Apache this can be done using
SciptAlias directive of `mod_alias`. The two CGI scripts are `admin.cgi.py`
and `computer.cgi.py`

A cron script `daily_cron.py` should be set to run daily. It is responsible of cleaning
old session files.

Initial database
----------------

Default database script creates two shifts and temporary superuser with
username "admin" and password "temporary". It is recommend to delete this
account when real superusers have been created. New users can also be directly
inserted into database on creation time. Passwords are encrypted using pyhons
crypt method of crypt module.

Configuration file
------------------

Configuration file is searched in this order

* Location specified by `CONFIG_FILE` environment variable
* From users home directory on `~/.config/computer_manager.json`
* From operating system configuration directory `/etc/computer_manager.json`
* From project root directory `computer_manager.json`. This means one level
   upper where the actual script file is located

Configuration file is JSON -formated file and it can hold following properties:

| variable name       | description                                           |
|---------------------|-------------------------------------------------------|
| `db_hostname`       | database server hostname                              |
| `db_username`       | database username                                     |
| `db_password`       | database password                                     |
| `db_database`       | database name on server                               |
| `time_format`       | local time format in python strftime format style     |
| `layout_directory`  | directory where layout files are located              |
| `session_directory` | directory to store session files                      |
| `lang`              | language code for default language                    |
| `user_levels`       | list of user type translations as dictionary with     |
|                     | level number as key and type name as value            |
| `floorplan`         | full filename to SVG image of floorplan. This is not  |
|                     | required for working installation                     |
| `viewbox`           | SCG ViewBox properties for floorplan                  |
| `path_admin`        | HTTP path of admin page ie `/admin`                   |
| `path_computers`    | HTTP path of computer management page                 |

The values of `shift_names` and `user_levels` are supposed to be moved into
database in future

User levels can vary and higher level can access all the data a lover one can.
Hard coded permissions are

| level | name     | description                                |
|-------|----------|--------------------------------------------|
| 200   | Admin    | All right, can create and manage new users |
| 100   | Manager  | Can view and change data                   |
| 50    | Observer | Can view data but not change it            |
| 0     | User     | Logged in user                             |

For users that are not logged in, user level is lover than zero.

Scripts and modules
-------------------

Binary directory content

| variable name      | purpose                                               |
|--------------------|-------------------------------------------------------|
| `computers.cgi.py` | the computer management CGI script                    |
| `admin.cgi.py`     | user management CGI script                            |
| `objects.py`       | module for handling the actual computer and user data |
| `database.py`      | module to handle MySQL database connections. It also  |
|                    | has methods for managing user accounts and logging in |
|                    | at the database level                                 |
| `web.py`           | methods for handling CGI sessions and a higher level  |
|                    | of user and session management                        |
| `hypertext.py`     | module for generating HTML data it has a method to    |
|                    | fill mustache notated layout pages and a method for   |
|                    | creating HTML forms                                   |
| `forms.json`       | JSON formated data for generating forms               |
| `lang-xx.json`     | language files in JSON format                         |

For this program all python scripts and static data like language and form
structures are located in `bin` directory. Executable CGI scripts are named
with .cgi.py -double extension. This helps text editors to identify them as
python scripts.

Language files are also in `bin` directory and they are named as lang-xx.json,
where xx is the language code. They are formed as simple dictionary table with
translation name as key in capital letters and translation as value. These
files are read by language code but at the moment allowed codes are hard coded
in the program

Default HTML layout files are located in layout -directory. For PHP scripts
there is a PHP include file in `php` directory.

