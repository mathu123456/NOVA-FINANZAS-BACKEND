from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date
from .. import models, auth
from ..database import get_db
from ..services.alert_service import generate_daily_alert, check_budget_alerts

router = APIRouter()

@router.get("/daily-summary")
def get_daily_summary_notification(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Genera el mensaje de alerta diaria"""
    return generate_daily_alert(db, current_user)

@router.get("/budget-alerts")
def get_budget_alerts_notification(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Verifica y genera alertas de presupuesto"""
    return check_budget_alerts(db, current_user)

@router.get("/check")
def check_notifications(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint principal que verifica todas las notificaciones"""
    
    # Verificar configuración
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()
    
    if not settings or not settings.alerts_enabled:
        return {"enabled": False, "alerts": []}
    
    # Verificar horario activo
    current_hour = datetime.utcnow().hour
    if not (settings.alert_start_hour <= current_hour <= settings.alert_end_hour):
        return {"enabled": True, "in_active_hours": False, "alerts": []}
    
    alerts = []
    
    # Alerta diaria
    daily = generate_daily_alert(db, current_user)
    if daily["message"]:
        alerts.append({
            "type": "daily_summary",
            "message": daily["message"],
            "data": daily
        })
    
    # Alertas de presupuesto
    budget_alerts = check_budget_alerts(db, current_user)
    for alert in budget_alerts:
        alerts.append({
            "type": "budget_alert",
            "message": alert["message"],
            "data": alert
        })
    
    return {
        "enabled": True,
        "in_active_hours": True,
        "alerts": alerts,
        "frequency_minutes": settings.alert_frequency_minutes
    }