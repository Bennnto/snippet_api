# Snippet API 
This project is a simple RESTful API for storing and managing code snippets, built with **FastAPI** and **SQLAlchemy**. <br>
It lets you create, read, update, and delete code snippets with a topic, optional description, and code body, all stored in a SQLite database.

## Features

- Create new code snippets with topic, description, and code
- List all stored snippets
- Retrieve a single snippet by ID
- Delete a snippet
- SQLite database for local or PostgreSQL with Render via SQLAlchemy ORM
- CORS enabled for easy frontend integration

## Application Structure
- main.py : Backend handle http method and database
- index.html : Frontend to submit a data or retrieve data from api
- addendum.html : Frontend to create index of code that store in database

## Usage and Installation

1. Clone the repository and open the project folder.

2. (Optional but recommended) Create and activate a virtual environment:

   macOS / Linux:
   ```bash
   python -m venv venv
   source venv/bin/activate
3. Install dependencies from requirements.txt
   
   ```bash
   pip install -r requirements.txt

4. Run Application Backend
   ```bash
   uvicorn main:app --reload

   or

   ```bash
   pip install "fastapi[standard]
   fastapi dev

5. Run frontend on local host 

   ```bash
   python3 -m http.server 8000

6. Access index.html by using localhost:8000/index.html
   
