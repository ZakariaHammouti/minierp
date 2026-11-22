from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from src.core import models as core_models  # noqa: F401
from src.einkauf import models as einkauf_models  # noqa: F401
from src.controlling import models as controlling_models  # noqa: F401

engine = create_engine(
    "sqlite:///data/minierp.db",
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    init_db()