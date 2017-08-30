[Table of contents generated using this app](https://tableofcontents.herokuapp.com)

- [Introduction](#introduction)
- [Usage](#usage)
  - [Setup](#setup)
  - [Running](#running)
    - [Diagnostics](#diagnostics)
  - [Accessing API docs:](#accessing-api-docs)
- [General Development](#general-development)
  - [Understanding the code](#understanding-the-code)
    - [Run code](#run-code)
      - [common package](#common-package)
- [ullekhanam](#ullekhanam)
  - [Intro](#intro)
  - [Development](#development)
    - [Root module](#root-module)
    - [Backend](#backend)
- [Textract](#textract)
  - [Intro](#intro)
  - [Development](#development)
    - [Root module](#root-module)
- [Guidelines](#guidelines)

# Introduction
Python based Web API's for the <vedavaapi.org> project.  

# Usage
## Setup
* We're currently using Python 2.7.
  * The installation procedure for the cv2 module with Python3.5 is fairly elaborate as of 20170423.
* Install various necessary python modules.
  * Refer to list in setup.py [Incomplete.]
* Grant the account running run.py authority to write in /opt/scan2text/.
  * sudo mkdir /opt/scan2text/; sudo mkdir /opt/scan2text/data; sudo chmod a+rwx /opt/scan2text
  * ln -s ~/vedavaapi_py_api/textract-example-repo/books /opt/scan2text/data/
* Install and setup mongo.
  * Add a user by running:
  ```
  use admin
  db.createUser( { user: "vedavaapiUser", pwd: "xyz", roles: [ { role: "dbAdminAnyDatabase", db: "admin" } , { role: "readWriteAnyDatabase", db: "admin" }] } )
  ```  
  * Create a server_config_local.json file based on the template provided.
* For further details of setting this app up in the context of the vedavaapi server, see [vedavaapi_misc](https://github.com/vedavaapi/vedavaapi-misc) .
* Special couchdb setup
  - We need to create these indices (perhaps using the fauxton UI):
  ```
  "fields": {
     targets.container_id: "asc"
  }
  ```
    - TODO This must be automated.

## Running
* Launch server: run.py

### Diagnostics
* List routes: /sitemap on your browser.

## REST API docs:
- Generally, just try the /docs/ path under the appropriate module. Example: [here](http://api.vedavaapi.org/py/textract/docs) .
- These links may be provided in various module-specific sections below.

# General Development
## Deveolopment guidelines
* **Don't write ugly code**.
  * Remember that your code will be read many more times than it will be written. Please take care.
  * Use meaningful identifier names (no naming global functions "myerror").
  * Follow the appropriate language-specific conventions for identifier naming and code formatting.
* **Document** well - use literate programming.
* **Don't reinvent the wheel** (Eg. Don't write your own logging module). Reuse and share code where possible.
* **Separate client and server** logic.
  * Avoid setting variables using flask templates. The js code should get data by making AJAX calls to the server.
  * In fact, one should be able to write (totally separate) pure html/ js code which will communicate with the server only using AJAX calls.
* Respect the **code structure**.
  * JS, python, html template code for different apps are in different directories.
* While designing **REST API**:
  * Read up and follow the best practices. When in doubt, discuss.
  * Currently we use flask restplus, and set the API docs to appear under the /doc/ path as described in the usage section.
* Be aware of **security**.
  * Don't leave the database open to all writes (even through API-s).
  * Do as much validation as possible when storing data.
* Plan **data backups**.
* **Data modeling and database interface** : See separate guidelines [here](https://github.com/sanskrit-coders/sanskrit_data).

## Understanding the code
* Can generate call graphs:
  * pyan.py --dot -c -e run.py |dot -Tpng > call_graphs/run.png

### Entry point
* [run.py]() :
  * starts the webservice
  * sets up actions to be taken when various URL-s are accessed.

### common package
* [flask_helper.py]()
  * Sets up the flask app.
  * Defines some basic handlers.
* [config.py]() contains various helper methods

# ullekhanam
## Intro
A general API to access and annotate a text corpus.

### API
- API docs [here](http://api.vedavaapi.org/py/ullekhanam/docs) .

## Development
### Root module
* [__init__.py]():
  * creates local temporary and data directories

### Backend
* db module with [db.py and collections.py]() :
  * Sets up database (an IndicDocs object) with initdb() and getdb()
  * Declares various other pymongo db collection containers, with methods for create /update / insert operations:
    * Books
    * Annotations

# Textract
## Intro
This is a web-based tool (based on the ullekhanam module) to rapidly decode scanned Indic document images into searchable text.

- It will enable users to identify and annotate characters in scanned document images and auto-identifies similar characters.

### REST API
See general notes from the ullekhanam module apply. Additional API docs [here](http://api.vedavaapi.org/py/textract/docs) .

## Development
See general notes from the ullekhanam module apply.

### Root module
* [__init__.py]():
  * creates local temporary and data directories
* [api_v1.py]():
  * Handles calls to /textract/*
