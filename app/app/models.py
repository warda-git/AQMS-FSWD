

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint
from app.database import Base

def now():
    return datetime.now(timezone.utc)

class Province(Base):
    __tablename__ = 'provinces'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)

class Region(Base):
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True)
    province_id = Column(Integer, ForeignKey('provinces.id'), nullable=False)
    name = Column(String(120), nullable=False)
    __table_args__ = (UniqueConstraint('province_id', 'name'),)

class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    name = Column(String(120), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    waqi_station_id = Column(String(120), nullable=True)
    __table_args__ = (UniqueConstraint('region_id', 'name'),)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(300), nullable=False)
    role = Column(String(30), nullable=False, default='citizen')
    province_id = Column(Integer, ForeignKey('provinces.id'), nullable=True)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)

class AQIReading(Base):
    __tablename__ = 'aqi_readings'
    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False, index=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=now, index=True)
    aqi = Column(Float, nullable=False)
    pm25 = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    no2 = Column(Float, nullable=True)
    co = Column(Float, nullable=True)
    source = Column(String(30), nullable=False, default='WAQI')
    __table_args__ = (
        UniqueConstraint('city_id', 'recorded_at', 'source'),
        CheckConstraint('aqi >= 0', name='ck_reading_aqi_nonnegative'),
    )

class Forecast(Base):
    __tablename__ = 'forecasts'
    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    forecast_for = Column(DateTime(timezone=True), nullable=False)
    predicted_aqi = Column(Float, nullable=False)
    model_version = Column(String(120), nullable=False, default='ridge-baseline-v1')
    generated_at = Column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint('predicted_aqi >= 0', name='ck_forecast_nonnegative'),)

class FavoriteCity(Base):
    __tablename__ = 'favorite_cities'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    __table_args__ = (UniqueConstraint('user_id','city_id'),)

class AlertRule(Base):
    __tablename__ = 'alert_rules'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    threshold_aqi = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    __table_args__ = (CheckConstraint('threshold_aqi >= 0', name='ck_alert_threshold_nonnegative'),)

class AlertHistory(Base):
    __tablename__ = 'alert_history'
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('alert_rules.id', ondelete='CASCADE'), nullable=False)
    reading_id = Column(Integer, ForeignKey('aqi_readings.id'), nullable=False)
    aqi_value = Column(Float, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=now)
    status = Column(String(40), nullable=False)
    __table_args__ = (UniqueConstraint('rule_id','reading_id'),)

class IncidentReport(Base):
    __tablename__ = 'incident_reports'
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(20), default='pending', nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)

class ResourceRequest(Base):
    __tablename__ = 'resource_requests'
    id = Column(Integer, primary_key=True)
    officer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    resource_type = Column(String(150), nullable=False)
    quantity = Column(Integer, nullable=False)
    justification = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    admin_remark = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint('quantity > 0', name='ck_request_quantity_positive'),)

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint('rating BETWEEN 1 AND 5', name='ck_feedback_rating_range'),)

class Advisory(Base):
    __tablename__ = 'advisories'
    id = Column(Integer, primary_key=True)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    aqi = Column(Float, nullable=False)
    generator_type = Column(String(30), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)
