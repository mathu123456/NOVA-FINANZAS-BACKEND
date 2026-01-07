from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.ExpenseResponse])
def get_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Expense).filter(
        models.Expense.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(models.Expense.date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(models.Expense.date <= datetime.combine(end_date, datetime.max.time()))
    if category_id:
        query = query.filter(models.Expense.category_id == category_id)
    
    expenses = query.order_by(models.Expense.date.desc()).offset(skip).limit(limit).all()
    return expenses

@router.get("/{expense_id}", response_model=schemas.ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    
    return expense

@router.post("/", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: schemas.ExpenseCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que la categoría existe y pertenece al usuario
    category = db.query(models.Category).filter(
        models.Category.id == expense.category_id,
        models.Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    
    db_expense = models.Expense(
        user_id=current_user.id,
        category_id=expense.category_id,
        amount=expense.amount,
        currency=expense.currency,
        note=expense.note,
        date=expense.date if expense.date else datetime.utcnow()
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@router.put("/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: schemas.ExpenseUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    
    # Actualizar campos
    if expense_update.amount is not None:
        expense.amount = expense_update.amount
    if expense_update.currency is not None:
        expense.currency = expense_update.currency
    if expense_update.category_id is not None:
        # Verificar que la nueva categoría existe
        category = db.query(models.Category).filter(
            models.Category.id == expense_update.category_id,
            models.Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )
        expense.category_id = expense_update.category_id
    if expense_update.note is not None:
        expense.note = expense_update.note
    if expense_update.date is not None:
        expense.date = expense_update.date
    
    db.commit()
    db.refresh(expense)
    return expense

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    
    db.delete(expense)
    db.commit()
    return None

@router.get("/today/summary", response_model=schemas.DailySummary)
def get_today_summary(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == current_user.id,
        models.Expense.date >= start_of_day,
        models.Expense.date <= end_of_day
    ).all()
    
    total = sum(e.amount for e in expenses)
    
    return {
        "date": today.isoformat(),
        "total": total,
        "currency": current_user.currency,
        "expenses_count": len(expenses)
    }