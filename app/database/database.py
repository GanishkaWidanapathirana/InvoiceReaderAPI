from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MYSQL_USER = os.getenv("CHOREO_INVOICE_DB_USERNAME")
MYSQL_PASSWORD = os.getenv("CHOREO_INVOICE_DB_PASSWORD")
MYSQL_HOST = os.getenv("CHOREO_INVOICE_DB_HOSTNAME")
MYSQL_PORT = os.getenv("CHOREO_INVOICE_DB_PORT")
MYSQL_DATABASE = os.getenv("CHOREO_INVOICE_DB_DATABASENAME")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        print("Database session created")  # Debug
        yield db
    except Exception as e:
        print("Database connection error:", str(e))
    finally:
        db.close()
        print("Database session closed")  # Debug
