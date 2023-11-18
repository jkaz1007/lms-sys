
# Leave Management System (LMS)

This is a simple Leave Management System built with FastAPI, MongoDB, and Pydantic.

## Getting Started

### Prerequisites

- Python 3.x installed (https://www.python.org/downloads/)
- MongoDB installed and running (https://www.mongodb.com/try/download/community)

### Clone the Repository

```bash
git clone https://github.com/jkaz1007/lms-sys.git
cd lms-sys/server
```
## Create Virtual Environment

### For Windows

```bash
python -m venv venv
venv\Scripts\activate
```
### For Linux/Mac
```bash
python -m venv venv
venv\Scripts\activate
```
## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure MongoDB

Make sure MongoDB is running, and update the MongoDB connection settings in app/database.py if needed. You can use either monogo compass or atlas.

```bash
# app/database.py

from pymongo import MongoClient

# Update the connection string based on your MongoDB configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["lms"]
```

## Run the Application

```bash
uvicorn app.main:app --reload
```
or
(since run.py contains uvicorn running script)
```bash
python run.py
```

The FastAPI application will be running at http://127.0.0.1:8000.

## API Documentation
Visit http://127.0.0.1:8000/docs to access the Swagger documentation and test the API endpoints.

## Project Structure

The project structure is organized as follows:

* app/: Contains the main FastAPI application code. \
    * main.py: Defines the FastAPI application and routes.
    * auth.py: Handles user authentication.
    * database.py: Manages the MongoDB connection.
    * models.py: Contains Pydantic models for data validation.
    * leave.py: Contains leave management logics and its API definations.
    * leaveTypes.py: Contains leaveTypes CRUD operations.
    * users.py: Contains auth API definations.
    * utils.py: Contains generic helper functions. Commonly used in different modules.
* requirements.txt: Lists project dependencies.
* run.py: Script to run the FastAPI server.
* README.md: Project documentation.


