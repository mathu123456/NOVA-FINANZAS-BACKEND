from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import models, schemas, auth
from ..database import get_db
from ..config import settings

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario o email ya registrado"
        )
    
    # Crear usuario
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        currency=user.currency,
        daily_limit=user.daily_limit
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Crear configuración por defecto
    user_settings = models.UserSettings(user_id=db_user.id)
    db.add(user_settings)
    
    # Crear categorías por defecto
    default_categories = [
        "Comida", "Transporte", "Entretenimiento", 
        "Servicios", "Educación", "Salud", "Otros"
    ]
    for cat_name in default_categories:
        category = models.Category(user_id=db_user.id, name=cat_name)
        db.add(category)
    
    db.commit()
    
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, user_credentials.username, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
def update_user(
    user_update: schemas.UserBase,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    current_user.currency = user_update.currency
    current_user.daily_limit = user_update.daily_limit
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/settings", response_model=schemas.UserSettingsResponse)
def get_user_settings(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    settings_obj = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()
    
    if not settings_obj:
        # Crear configuración por defecto si no existe
        settings_obj = models.UserSettings(user_id=current_user.id)
        db.add(settings_obj)
        db.commit()
        db.refresh(settings_obj)
    
    return settings_obj

@router.put("/settings", response_model=schemas.UserSettingsResponse)
def update_user_settings(
    settings_update: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    settings_obj = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.id
    ).first()
    
    if not settings_obj:
        settings_obj = models.UserSettings(user_id=current_user.id)
        db.add(settings_obj)
    
    # Actualizar campos
    if settings_update.theme is not None:
        settings_obj.theme = settings_update.theme
    if settings_update.alerts_enabled is not None:
        settings_obj.alerts_enabled = settings_update.alerts_enabled
    if settings_update.alert_frequency_minutes is not None:
        settings_obj.alert_frequency_minutes = settings_update.alert_frequency_minutes
    if settings_update.alert_start_hour is not None:
        settings_obj.alert_start_hour = settings_update.alert_start_hour
    if settings_update.alert_end_hour is not None:
        settings_obj.alert_end_hour = settings_update.alert_end_hour
    
    db.commit()
    db.refresh(settings_obj)
    return settings_obj