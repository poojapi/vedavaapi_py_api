**[Table of Contents](http://tableofcontent.eu)**
<!-- Table of contents generated generated by http://tableofcontent.eu -->
- [Introduction](#introduction)
- [Usage](#usage)
  - [Documentation (includes setup instructions)](#documentation-includes-setup-instructions)
  - [API](#api)
- [For contributors](#for-contributors)
  - [Contact](#contact)
  - [Document generation](#document-generation)
  - [Deveolopment guidelines](#deveolopment-guidelines)
  - [Understanding the code](#understanding-the-code)

# Introduction
Python based Web API's for the <vedavaapi.org> project.

# Usage
## Documentation (includes setup instructions)
- http://vedavaapi-py-api.readthedocs.io/en/latest/vedavaapi_py_api.html should automatically have good updated documentation - unless there are build errors.

## API
- ullekhanam API docs [here](http://api.vedavaapi.org/py/ullekhanam/docs) - includes:
  - links to a [video playlist](https://www.youtube.com/playlist?list=PL63uIhJxWbghuZDlqwRLpPoPPFDNQppR6) describing API usage and schema.
  - JSON-schemas
- Textract API docs [here](http://api.vedavaapi.org/py/textract/docs) .
- User/ Oauth API docs [here](http://api.vedavaapi.org/py/textract/docs) .

# For contributors
Please refer to the documentation pages linked above to get an idea about the layout of this simple module - or just look at the code. This project depends on [sanskrit_data](https://github.com/vedavaapi/sanskrit_data/) and [docimage](https://github.com/vedavaapi/docimage/) - documentation for those may also be of interest to you. 

## Contact
Have a problem or question? Please head to [github](https://github.com/vedavaapi/vedavaapi_py_api).

## Document generation
- To the extant possible, we keep documentation together with the code - this deters divergence between them.
- Set up sphynx with `sudo pip3 install -U sphinx`
- Sphynx html docs can be generated with `cd docs; make html`

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
* **Data modeling and database interface** : See separate guidelines [here](https://github.com/vedavaapi/sanskrit_data).

## Understanding the code
* Can generate call graphs:
  * pyan.py --dot -c -e run.py |dot -Tpng > call_graphs/run.png
