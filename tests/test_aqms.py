
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Province, Region, City, AQIReading, Forecast
)
from app.crud import (
    create_user, add_favorite, get_favorites,
    remove_favorite, save_aqi_reading, get_latest_aqi
)
from app.forecasting import forecast_aqi
from app.forecast_storage import save_forecast


@pytest.fixture
def db():
    # Temporary test database, not the real database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    province = Province(name="Punjab")
    session.add(province)
    session.flush()

    region = Region(
        name="Lahore Division",
        province_id=province.id
    )
    session.add(region)
    session.flush()

    session.add(City(
        name="Lahore",
        region_id=region.id,
        latitude=31.5204,
        longitude=74.3587
    ))
    session.commit()

    yield session

    session.close()
    engine.dispose()


def add_test_readings(db, city_id):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for hour in range(140):
        db.add(AQIReading(
            city_id=city_id,
            recorded_at=start + timedelta(hours=hour),
            aqi=100 + (hour % 24),
            source="SYNTHETIC_TEST"
        ))

    db.commit()


def test_database_tables(db):
    tables = inspect(db.bind).get_table_names()

    assert len(tables) == 13
    assert "users" in tables
    assert "cities" in tables
    assert "aqi_readings" in tables
    assert "forecasts" in tables


def test_user_and_favorites(db):
    user = create_user(
        db, "Test User", "test@example.com",
        password_hash="test-only-hash"
    )

    city = db.query(City).first()

    add_favorite(db, user.id, city.id)
    add_favorite(db, user.id, city.id)

    favorites = get_favorites(db, user.id)
    assert len(favorites) == 1

    assert remove_favorite(db, user.id, city.id)
    assert len(get_favorites(db, user.id)) == 0


def test_aqi_reading(db):
    city = db.query(City).first()

    save_aqi_reading(
        db, city.id, 150,
        source="SYNTHETIC_TEST"
    )

    latest = get_latest_aqi(db, city.id)
    assert latest.aqi == 150


def test_invalid_aqi(db):
    city = db.query(City).first()

    with pytest.raises(ValueError):
        save_aqi_reading(db, city.id, -20)


def test_forecasting(db):
    city = db.query(City).first()
    add_test_readings(db, city.id)

    result = forecast_aqi(db, "Lahore", 24)

    assert result["model"] == "Ridge Regression"
    assert len(result["forecast"]) == 24
    assert result["mae"] >= 0
    assert result["rmse"] >= 0


def test_forecast_database_storage(db):
    city = db.query(City).first()
    add_test_readings(db, city.id)

    result, count = save_forecast(db, "Lahore", 24)

    assert count == 24
    assert len(result["forecast"]) == 24
    assert db.query(Forecast).count() == 24

    # Rerun should update, not duplicate records
    save_forecast(db, "Lahore", 24)
    assert db.query(Forecast).count() == 24
