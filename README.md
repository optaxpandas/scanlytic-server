# Scanlytic
This is a Django server developed using **Python 3.12.x** powered with **PostgreSQL** for the database

## Setup
This server consists of 3 apps
- **scanlytic** - The app consisting of all the required settings & urls
- **server** - This app consists of the User related APIs
- **table_extractor** - This app consists of Table Extraction related APIs

### Create Virtual Environment
- Create virtual environment `python -m venv <environment-name>`
- Activate the virtual environment `<environment-name/Scripts/active`

### Install Dependencies
Run `pip install -r requirements.txt`

### Clone This Repository
`git clone https://github.com/optaxpandas/scanlytic-server.git`

### Environment Variables
Copy the .env.example to .env


| Variable Name       | Description                  | Value                    |
| ------------------- | ---------------------------- | ------------------------ |
| `DATABASE_NAME`     | Name of the database         | `your-database-name`     |
| `DATABASE_USER`     | Database user                | `your-database-user`     |
| `DATABASE_PASSWORD` | Password of the database     | `your-database-password` |
| `HOST`              | Host address of the database | `localhost`              |
| `PORT`              | Port of the database         | `5432`                   |


### Migrations
To create the database schema 
- Move into the server directory `cd scanlytic`
- Run `py manage.py makemigrations`
- Run `py manage.py migrate`

### Run Server
To run the server within the server directory, run `py manage.py runserver`
