
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import User, City, FavoriteCity, AQIReading


# -------- USER OPERATIONS --------

def create_user(db: Session, name, email, password_hash):
    email = email.strip().lower()

    existing = db.query(User).filter_by(email=email).first()

    if existing:
        raise ValueError("Email already registered")

    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        role="citizen"
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id):
    return db.query(User).filter_by(id=user_id).first()


def get_user_by_email(db: Session, email):
    return db.query(User).filter_by(
        email=email.strip().lower()
    ).first()


# -------- CITY OPERATIONS --------

def get_all_cities(db: Session):
    return db.query(City).order_by(City.name).all()


def get_city(db: Session, city_id):
    return db.query(City).filter_by(id=city_id).first()


# -------- FAVORITE CITIES --------

def add_favorite(db: Session, user_id, city_id):
    if not get_user(db, user_id):
        raise ValueError("User not found")

    if not get_city(db, city_id):
        raise ValueError("City not found")

    existing = db.query(FavoriteCity).filter_by(
        user_id=user_id,
        city_id=city_id
    ).first()

    if existing:
        return existing

    favorite = FavoriteCity(
        user_id=user_id,
        city_id=city_id
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def get_favorites(db: Session, user_id):
    return db.query(City).join(
        FavoriteCity,
        FavoriteCity.city_id == City.id
    ).filter(
        FavoriteCity.user_id == user_id
    ).all()


def remove_favorite(db: Session, user_id, city_id):
    favorite = db.query(FavoriteCity).filter_by(
        user_id=user_id,
        city_id=city_id
    ).first()

    if not favorite:
        return False

    db.delete(favorite)
    db.commit()
    return True


# -------- AQI OPERATIONS --------

def save_aqi_reading(
    db: Session,
    city_id,
    aqi,
    recorded_at=None,
    pm25=None,
    pm10=None,
    source="WAQI"
):
    if not get_city(db, city_id):
        raise ValueError("City not found")

    if aqi < 0:
        raise ValueError("AQI cannot be negative")

    if recorded_at is None:
        recorded_at = datetime.now(timezone.utc)

    reading = AQIReading(
        city_id=city_id,
        aqi=aqi,
        recorded_at=recorded_at,
        pm25=pm25,
        pm10=pm10,
        source=source
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_latest_aqi(db: Session, city_id):
    return db.query(AQIReading).filter_by(
        city_id=city_id
    ).order_by(
        AQIReading.recorded_at.desc()
    ).first()


def get_aqi_history(db: Session, city_id, limit=100):
    return db.query(AQIReading).filter_by(
        city_id=city_id
    ).order_by(
        AQIReading.recorded_at.desc()
    ).limit(limit).all()
