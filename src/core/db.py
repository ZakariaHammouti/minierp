from sqlmodel import SQLModel, create_engine

from src.core import models  # noqa: F401 – damit die Tabellen bekannt sind

engine = create_engine("sqlite:///data/minierp.db", echo=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()