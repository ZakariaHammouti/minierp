from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session

from src.core.db import get_session
from src.core.models import Mandant

SessionDep = Annotated[Session, Depends(get_session)]


def get_mandant_id(session: SessionDep, x_mandant: Annotated[int, Header()]) -> int:
    if session.get(Mandant, x_mandant) is None:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")
    return x_mandant


MandantDep = Annotated[int, Depends(get_mandant_id)]