
from datetime import datetime, timedelta, timezone
import argparse
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.database import SessionLocal
from app.models import City, AQIReading


def load_hourly_data(db, city_id):
    readings = (
        db.query(AQIReading)
        .filter(AQIReading.city_id == city_id)
        .order_by(AQIReading.recorded_at)
        .all()
    )

    # Keep one reading per UTC hour
    hourly = {}

    for reading in readings:
        date = reading.recorded_at

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        date = date.astimezone(timezone.utc)
        date = date.replace(
            minute=0, second=0, microsecond=0
        )

        value = float(reading.aqi)

        if np.isfinite(value) and value >= 0:
            hourly[date] = value

    ordered = sorted(hourly.items())

    if not ordered:
        raise ValueError("No AQI data found for this city")

    # Use the latest continuous hourly observations
    continuous = [ordered[-1]]

    for item in reversed(ordered[:-1]):
        previous_hour = continuous[-1][0] - timedelta(hours=1)

        if item[0] != previous_hour:
            break

        continuous.append(item)

    continuous.reverse()

    if len(continuous) < 96:
        raise ValueError(
            "At least 96 consecutive hourly AQI readings "
            "are required for forecasting"
        )

    dates = [item[0] for item in continuous]
    values = [item[1] for item in continuous]

    return dates, values


def make_features(history, hour):
    # Previous AQI values help predict the next hour
    return [
        history[-1],
        history[-2],
        history[-3],
        history[-6],
        history[-24],
        np.sin(2 * np.pi * hour / 24),
        np.cos(2 * np.pi * hour / 24)
    ]


def forecast_aqi(db, city_name, hours=48):

    if hours not in (24, 48):
        raise ValueError("Hours must be 24 or 48")

    city = db.query(City).filter(
        City.name.ilike(city_name)
    ).first()

    if city is None:
        raise ValueError("City not found")

    dates, values = load_hourly_data(db, city.id)

    X = []
    y = []

    for i in range(24, len(values)):
        X.append(
            make_features(values[:i], dates[i].hour)
        )
        y.append(values[i])

    X = np.array(X)
    y = np.array(y)

    # Chronological train/test split
    split = int(len(X) * 0.8)

    model = Ridge(alpha=1.0)
    model.fit(X[:split], y[:split])

    test_predictions = model.predict(X[split:])

    mae = mean_absolute_error(
        y[split:], test_predictions
    )

    rmse = np.sqrt(
        mean_squared_error(y[split:], test_predictions)
    )

    # Retrain on all available observations
    model.fit(X, y)

    history = list(values)
    last_date = dates[-1]
    predictions = []

    for step in range(1, hours + 1):
        next_date = last_date + timedelta(hours=step)

        features = make_features(
            history, next_date.hour
        )

        predicted = float(
            model.predict([features])[0]
        )

        predicted = max(0.0, predicted)
        predicted = round(predicted, 2)

        predictions.append({
            "forecast_for": next_date.isoformat(),
            "predicted_aqi": predicted
        })

        # Use prediction for subsequent forecast hours
        history.append(predicted)

    return {
        "city": city.name,
        "last_observation": last_date.isoformat(),
        "model": "Ridge Regression",
        "mae": round(float(mae), 2),
        "rmse": round(float(rmse), 2),
        "evaluation": "One-hour-ahead holdout",
        "forecast": predictions
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--city", required=True)
    parser.add_argument(
        "--hours", type=int, default=48
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        result = forecast_aqi(
            db, args.city, args.hours
        )

        print("City:", result["city"])
        print("Model:", result["model"])
        print("MAE:", result["mae"])
        print("RMSE:", result["rmse"])

        for row in result["forecast"]:
            print(
                row["forecast_for"],
                row["predicted_aqi"]
            )

    finally:
        db.close()
