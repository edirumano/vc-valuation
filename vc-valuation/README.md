# vc-valuation

This is a Flask project that provides a web interface for managing investments. The application allows users to create new investments, view existing investments, and update or delete existing investments.

## Installation

1. Clone the repository:
```bash
$ git clone https://github.com/yourusername/flask-project.git
$ cd flask-project
```

2. Create a virtual environment and activate it:
```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

3. Install the dependencies:

```bash
$ pip install -r requirements.txt
```

## Configuration
The application can be configured by setting environment variables or by creating a config.py file in the project root directory. The following environment variables are available:

* FLASK_APP: The name of the Flask application. Default is app.
* FLASK_ENV: The environment in which the application is running. Possible values are development, production, and testing. Default is development.
* DATABASE_URL: The URL of the database used by the application. Default is sqlite:///data.db.
* SECRET_KEY: The secret key used by the application for encryption. Default is supersecretkey.

To use a config.py file, create a file with the following structure:

```python
import os

class Config:
    FLASK_APP = os.environ.get('FLASK_APP', 'app')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///data.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
```

Running the Application
To run the application, use the following command:

```bash
$ flask run
```
The application will be available at http://localhost:5000.

Testing
To run the tests, use the following command:

```bash
$ pytest
```

Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

License
This project is licensed under the MIT License - see the LICENSE file for details.
