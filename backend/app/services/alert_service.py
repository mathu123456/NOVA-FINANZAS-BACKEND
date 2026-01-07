from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from .. import models

def generate_daily_alert(db: Session, user: models.User):
    """Genera el resumen de gastos del día"""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    # Obtener gastos del día
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user.id,
        models.Expense.date >= start_of_day,
        models.Expense.date <= end_of_day
    ).all()
    
    total = sum(e.amount for e in expenses)
    count = len(expenses)
    
    # Generar mensaje
    if count == 0:
        message = "No has registrado gastos hoy. ¡Recuerda llevar tu registro!"
    else:
        message = f"Hoy llevas gastado {user.currency} {total:.2f} en {count} transacciones"
        
        # Verificar límite diario
        if user.daily_limit > 0:
            percentage = (total / user.daily_limit) * 100
            if percentage >= 100:
                message += f" ⚠️ Has superado tu límite diario ({user.currency} {user.daily_limit:.2f})"
            elif percentage >= 80:
                message += f" ⚠️ Has usado el {percentage:.0f}% de tu límite diario"
    
    return {
        "message": message,
        "total": total,
        "count": count,
        "currency": user.currency,
        "daily_limit": user.daily_limit,
        "limit_exceeded": total > user.daily_limit if user.daily_limit > 0 else False
    }

def check_budget_alerts(db: Session, user: models.User):
    """Verifica alertas de presupuesto mensual"""
    now = datetime.utcnow()
    month = now.month
    year = now.year
    
    # Obtener presupuestos del mes
    budgets = db.query(models.Budget).filter(
        models.Budget.user_id == user.id,
        models.Budget.month == month,
        models.Budget.year == year
    ).all()
    
    if not budgets:
        return []
    
    # Calcular fechas del período
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    alerts = []
    
    for budget in budgets:
        # Calcular gastos
        query = db.query(func.sum(models.Expense.amount)).filter(
            models.Expense.user_id == user.id,
            models.Expense.date >= start_date,
            models.Expense.date < end_date
        )
        
        category_name = "Global"
        if budget.category_id:
            query = query.filter(models.Expense.category_id == budget.category_id)
            category = db.query(models.Category).filter(
                models.Category.id == budget.category_id
            ).first()
            if category:
                category_name = category.name
        
        spent = query.scalar() or 0.0
        percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
        
        # Generar alertas según porcentaje
        message = None
        if percentage >= 100:
            message = f"⚠️ Presupuesto {category_name} superado: {user.currency} {spent:.2f} de {user.currency} {budget.amount:.2f} ({percentage:.0f}%)"
        elif percentage >= 75:
            message = f"⚠️ Presupuesto {category_name} al {percentage:.0f}%: {user.currency} {spent:.2f} de {user.currency} {budget.amount:.2f}"
        elif percentage >= 50:
            message = f"Presupuesto {category_name} al {percentage:.0f}%: {user.currency} {spent:.2f} de {user.currency} {budget.amount:.2f}"
        
        if message:
            alerts.append({
                "message": message,
                "category": category_name,
                "spent": spent,
                "budget": budget.amount,
                "percentage": round(percentage, 2),
                "exceeded": percentage >= 100
            })
    
    return alerts