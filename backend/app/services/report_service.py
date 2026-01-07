from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from .. import models

def generate_category_summary(db: Session, user_id: int, month: int, year: int):
    """Genera resumen de gastos por categoría"""
    # Calcular fechas del período
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Obtener gastos agrupados por categoría
    results = db.query(
        models.Category.name,
        func.sum(models.Expense.amount).label('total')
    ).join(
        models.Expense, models.Expense.category_id == models.Category.id
    ).filter(
        models.Expense.user_id == user_id,
        models.Expense.date >= start_date,
        models.Expense.date < end_date
    ).group_by(models.Category.name).all()
    
    # Calcular total general
    total_general = sum(r.total for r in results)
    
    # Construir respuesta
    summary = []
    for category_name, total in results:
        percentage = (total / total_general * 100) if total_general > 0 else 0
        summary.append({
            "category_name": category_name,
            "total": round(total, 2),
            "percentage": round(percentage, 2)
        })
    
    # Ordenar por total descendente
    summary.sort(key=lambda x: x['total'], reverse=True)
    
    return summary

def calculate_comparative_report(db: Session, user_id: int):
    """Calcula reporte comparativo de gastos"""
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year
    
    # Mes actual
    start_current = datetime(current_year, current_month, 1)
    if current_month == 12:
        end_current = datetime(current_year + 1, 1, 1)
    else:
        end_current = datetime(current_year, current_month + 1, 1)
    
    current_total = db.query(func.sum(models.Expense.amount)).filter(
        models.Expense.user_id == user_id,
        models.Expense.date >= start_current,
        models.Expense.date < end_current
    ).scalar() or 0.0
    
    # Mes anterior
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year
    
    start_prev = datetime(prev_year, prev_month, 1)
    if prev_month == 12:
        end_prev = datetime(prev_year + 1, 1, 1)
    else:
        end_prev = datetime(prev_year, prev_month + 1, 1)
    
    previous_total = db.query(func.sum(models.Expense.amount)).filter(
        models.Expense.user_id == user_id,
        models.Expense.date >= start_prev,
        models.Expense.date < end_prev
    ).scalar() or 0.0
    
    # Calcular diferencia con mes anterior
    diff_absolute = current_total - previous_total
    diff_percentage = (diff_absolute / previous_total * 100) if previous_total > 0 else 0
    
    # Promedio últimos 3 meses
    totals_last_3 = []
    for i in range(3):
        m = current_month - i
        y = current_year
        while m <= 0:
            m += 12
            y -= 1
        
        start = datetime(y, m, 1)
        if m == 12:
            end = datetime(y + 1, 1, 1)
        else:
            end = datetime(y, m + 1, 1)
        
        total = db.query(func.sum(models.Expense.amount)).filter(
            models.Expense.user_id == user_id,
            models.Expense.date >= start,
            models.Expense.date < end
        ).scalar() or 0.0
        
        totals_last_3.append(total)
    
    average_3_months = sum(totals_last_3) / 3
    diff_vs_average = current_total - average_3_months
    
    return {
        "current_month_total": round(current_total, 2),
        "previous_month_total": round(previous_total, 2),
        "difference_absolute": round(diff_absolute, 2),
        "difference_percentage": round(diff_percentage, 2),
        "average_last_3_months": round(average_3_months, 2),
        "difference_vs_average": round(diff_vs_average, 2)
    }