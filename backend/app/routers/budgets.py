from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.BudgetResponse])
def get_budgets(
    month: int = None,
    year: int = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id
    )
    
    if month:
        query = query.filter(models.Budget.month == month)
    if year:
        query = query.filter(models.Budget.year == year)
    
    budgets = query.all()
    return budgets

@router.post("/", response_model=schemas.BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget: schemas.BudgetCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar si ya existe un presupuesto para ese mes/año/categoría
    existing = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id,
        models.Budget.month == budget.month,
        models.Budget.year == budget.year,
        models.Budget.category_id == budget.category_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un presupuesto para este período y categoría"
        )
    
    # Si tiene category_id, verificar que existe
    if budget.category_id:
        category = db.query(models.Category).filter(
            models.Category.id == budget.category_id,
            models.Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada"
            )
    
    db_budget = models.Budget(
        user_id=current_user.id,
        category_id=budget.category_id,
        amount=budget.amount,
        month=budget.month,
        year=budget.year
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.put("/{budget_id}", response_model=schemas.BudgetResponse)
def update_budget(
    budget_id: int,
    budget_update: schemas.BudgetUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(models.Budget).filter(
        models.Budget.id == budget_id,
        models.Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presupuesto no encontrado"
        )
    
    if budget_update.amount is not None:
        budget.amount = budget_update.amount
    
    db.commit()
    db.refresh(budget)
    return budget

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(models.Budget).filter(
        models.Budget.id == budget_id,
        models.Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presupuesto no encontrado"
        )
    
    db.delete(budget)
    db.commit()
    return None

@router.get("/status", response_model=List[schemas.BudgetStatus])
def get_budget_status(
    month: int = None,
    year: int = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Usar mes y año actual si no se especifican
    if not month or not year:
        now = datetime.utcnow()
        month = now.month
        year = now.year
    
    # Obtener presupuestos del período
    budgets = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id,
        models.Budget.month == month,
        models.Budget.year == year
    ).all()
    
    # Calcular fechas del período
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    result = []
    
    for budget in budgets:
        # Calcular gastos del período
        query = db.query(func.sum(models.Expense.amount)).filter(
            models.Expense.user_id == current_user.id,
            models.Expense.date >= start_date,
            models.Expense.date < end_date
        )
        
        if budget.category_id:
            query = query.filter(models.Expense.category_id == budget.category_id)
            category_name = db.query(models.Category.name).filter(
                models.Category.id == budget.category_id
            ).scalar()
        else:
            category_name = None
        
        spent = query.scalar() or 0.0
        remaining = budget.amount - spent
        percentage_used = (spent / budget.amount * 100) if budget.amount > 0 else 0
        
        result.append({
            "budget_amount": budget.amount,
            "spent": spent,
            "remaining": remaining,
            "percentage_used": round(percentage_used, 2),
            "is_exceeded": spent > budget.amount,
            "category_name": category_name
        })
    
    return result