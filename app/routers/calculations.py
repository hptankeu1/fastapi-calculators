"""Calculation BREAD endpoints. Every route is scoped to the logged-in user."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Calculation, User
from app.operations import compute
from app.schemas import CalculationCreate, CalculationRead, CalculationUpdate

router = APIRouter(prefix="/calculations", tags=["calculations"])


def _get_owned(calc_id: int, user: User, db: Session) -> Calculation:
    calc = db.get(Calculation, calc_id)
    if calc is None or calc.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Calculation not found")
    return calc


# Browse
@router.get("", response_model=list[CalculationRead])
def browse(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Calculation).where(Calculation.user_id == user.id).order_by(Calculation.id)
    return db.scalars(stmt).all()


# Read
@router.get("/{calc_id}", response_model=CalculationRead)
def read(calc_id: int, db: Session = Depends(get_db),
         user: User = Depends(get_current_user)):
    return _get_owned(calc_id, user, db)


# Add
@router.post("", response_model=CalculationRead, status_code=status.HTTP_201_CREATED)
def add(payload: CalculationCreate, db: Session = Depends(get_db),
        user: User = Depends(get_current_user)):
    calc = Calculation(
        type=payload.type.value,
        a=payload.a,
        b=payload.b,
        result=compute(payload.type, payload.a, payload.b),
        user_id=user.id,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


def _apply_update(calc: Calculation, payload: CalculationUpdate, db: Session) -> Calculation:
    new_type = payload.type.value if payload.type is not None else calc.type
    new_a = payload.a if payload.a is not None else calc.a
    new_b = payload.b if payload.b is not None else calc.b
    try:
        result = compute(new_type, new_a, new_b)
    except ZeroDivisionError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Cannot divide by zero")
    calc.type, calc.a, calc.b, calc.result = new_type, new_a, new_b, result
    db.commit()
    db.refresh(calc)
    return calc


# Edit (PUT and PATCH both accept partial updates and recompute the result)
@router.put("/{calc_id}", response_model=CalculationRead)
@router.patch("/{calc_id}", response_model=CalculationRead)
def edit(calc_id: int, payload: CalculationUpdate, db: Session = Depends(get_db),
         user: User = Depends(get_current_user)):
    return _apply_update(_get_owned(calc_id, user, db), payload, db)


# Delete
@router.delete("/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(calc_id: int, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    db.delete(_get_owned(calc_id, user, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
