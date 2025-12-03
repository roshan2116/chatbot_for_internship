from sqlmodel import SQLModel, create_engine

MYSQL_URL = "mysql+mysqlconnector://root:root@localhost/chatbot_database"

engine = create_engine(MYSQL_URL, echo=True)

def create_db():
    SQLModel.metadata.create_all(engine)
