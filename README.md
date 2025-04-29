![CI/CD](https://github.com/software-students-spring2025/5-final-error404/actions/workflows/app-cicd.yml/badge.svg)

# Documentation

This app allows users to use their webcam to scan barcodes of books and/or search them up to add to their virtual library. They can then organize these books between "Want to Read" and "Books Read." If you ever find a book out in public or in the library that you want to keep track of and remember, this is a great application for that!

## Installation

### Running on Any Platform
Windows: Use PowerShell, ensure `pip` and `git` are installed. <br />
macOS: Use Terminal, ensure `brew` or `pip` is updated. <br />
Linux: Use `bash`, ensure `python3` and `pipenv` are installed.


## Usage Guide

### 1. Set Up a Virtual Environment
```
python3 -m venv error404
source error404/bin/activate
```

### 2. Install Dependencies
pip install all of these packages:
```
pip3 install opencv-python
pip3 install flask
pip3 install flask-login
pip3 install numpy
pip3 install pymongo
pip3 install mongomock
pip3 install python-dotenv
pip3 install requests
python3 -m pip install coverage
pip3 install pytest
```
or you can just do:
```
pip3 install -r requirements.txt
```

Copy the provided `env.example` file to `.env` in the project root and fill in the information with your own `URI`, `DBNAME`, and `SECRET_KEY` (or check the error404 team channel on Discord to get access to our database). <br />

env.example file:
```
# MongoDB connection string (must begin with mongodb+srv:// or mongodb://)
URI=mongodb+srv://<username>:<password>@<your-cluster>.mongodb.net/?retryWrites=true&w=majority&appName=virtualLibrary

# Name for MongoDB Database
DBNAME=virtualLibrary

# Flask secret key for session management
SECRET_KEY=your-secret-key-here

```

To downlaod and setup docker:
```
brew install docker-compose         # download docker for macOS
sudo apt install docker-compose     # download docker for Windows

docker-compose up --build           # run the docker containers
```

To run the program, use:
```
python3 app.py
```

### 3. Run Tests
Ensure everything works - make sure you are in the correct directories before running these commands:
```
# For tests:

pytest

# For coverage:

coverage run -m pytest
coverage report
```

## Dockerhub
Either one of these dockerhub links can be used - multiple group members uploaded the images:
1. [🔗 errorlibrary-app](https://hub.docker.com/r/syed1naqvi/errorlibrary-app)<br/>
2. [🔗 errorlibrary-app](https://hub.docker.com/r/mahmouds1201/errorlibrary-app)

## Team Members
[Mahmoud Shehata](https://github.com/MahmoudS1201) <br /> 
[Marcos Huh](https://github.com/mh6355) <br />
[Catherine Huang](https://github.com/Catherine1342) <br />
[Syed Naqvi](https://github.com/syed1naqvi)

## License
This project is licensed under the GNU General Public License. See the [LICENSE](https://github.com/software-students-spring2025/5-final-error404/blob/main/LICENSE) file for details.