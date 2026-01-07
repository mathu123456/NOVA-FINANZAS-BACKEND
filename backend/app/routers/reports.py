from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
from .. import models, schemas, auth
from ..database import get_db
from ..services.report_service import generate_category_summary, calculate_comparative_report
from ..services.export_service import export_to_pdf, export_to_excel

router = APIRouter()

@router.get("/categories", response_model=List[schemas.CategorySummary])
def get_category_summary(
    month: int = None,
    year: int = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not month or not year:
        now = datetime.utcnow()
        month = now.month
        year = year if year else now.year
    
    return generate_category_summary(db, current_user.id, month, year)

@router.get("/comparative", response_model=schemas.ComparativeReport)
def get_comparative_report(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return calculate_comparative_report(db, current_user.id)

@router.get("/export/pdf")
def export_report_pdf(
    start_date: str = None,
    end_date: str = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Parsear fechas
    if start_date:
        start = datetime.fromisoformat(start_date)
    else:
        start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
    else:
        end = datetime.utcnow()
    
    # Obtener gastos
    expenses = db.query(models.Expense).filter(
        models.Expense.user_id == current_user.id,
        models.Expense.date >= start,
        models.Expense.date <= end
    ).all()
    
    # Generar PDF
    pdf_bytes = export_to_pdf(expenses, current_user, start, end)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=reporte_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.pdf"
        }
    )

@router.get("/export/excel")
def export_report_excel(
    start_date: str = None,
    end_date: str = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Parsear fechas
    if start_date:
        start = datetime.fromisoformat(start_date)
    else:
        start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
    else:
        end = datetime.utcnow()
    
    # Obtener gastos con categorías
    expenses = db.query(models.Expense, models.Category.name).join(
        models.Category, models.Expense.category_id == models.Category.id
    ).filter(
        models.Expense.user_id == current_user.id,
        models.Expense.date >= start,
        models.Expense.date <= end
    ).all()
    
    # Generar Excel
    excel_bytes = export_to_excel(expenses, start, end)
    
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=gastos_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.xlsx"
        }
    )