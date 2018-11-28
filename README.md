Computer and user management scrip
==================================

This collection of script was created for computer occupation management for
Tampere Syke. It has simple login and user management system and of course the
computer and people management system. User account database uses MySQL but at
the moment all computer and people data is stored as JSON files.

Implementation to server
------------------------

It is recommended to have scripts and data outsite the public html directory
and linking or aliasing them to server. With Apache this can be done using
SciptAlias directive of mod_alias.

Program structure
-----------------



Scripts and modules
-------------------

Python scrips and other _hard coded_ data is located in bin -directory, default
HTML layout is in layout -directory and PHP include file is in php -directory.
Python CGI scripts are named with .cgi.py -double file extension.

* *bin/computers.cgi.py* is the actual computer management CGI script

* *bin/admin.cgi.py* is file is user management CGI script

* *objects.py* is mode for handling the actual computer and user data

* *database.py* is module to handle MySQL database connections. It also has
   methods for managing user accounts and logging in at the database level

* *web.py* has methods for handling CGI sessions and a higher level of user and
   session management

* *hypertext.py* is module for generating HTML data it has a method to fill
   mustache notated layout pages and a method for creating HTML forms

* *forms.json* is JSON formated data for generating forms

* *lang-xx.json* files are language files in JSON format

