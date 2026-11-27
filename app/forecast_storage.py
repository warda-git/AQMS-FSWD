
import argparse
from datetime import datetime, timezone

from app.database import SessionLocal, create_tables
from app.models import City, Forecast
from app.forecasting import forecast_aqi


MODEL_VERSION = "ridge-baseline-v1"


def save_forecast(db, city_name, hours=48):

    # Step 1: Generate predictions using scikit-learn
    result = forecast_aqi(db, city_name, hours)

    # Step 2: Find city in database
    city = db.query(City).filter(
        City.name.ilike(city_name)
    ).first()

    if city is None:
        raise ValueError("City not found")

    saved = 0

    try:
        # Step 3: Save each hourly prediction
        for row in result["forecast"]:

            forecast_time = datetime.fromisoformat(
                row["forecast_for"]
            ).astimezone(timezone.utc)

            predicted_aqi = row["predicted_aqi"]

            # Check whether prediction already exists
            existing = db.query(Forecast).filter_by(
                city_id=city.id,
                forecast_for=forecast_time,
                model_version=MODEL_VERSION
            ).first()

            if existing:
                # Update previous prediction
                existing.predicted_aqi = predicted_aqi
                existing.generated_at = datetime.now(
                    timezone.utc
                )

            else:
                # Create a new forecast record
                forecast = Forecast(
                    city_id=city.id,
                    forecast_for=forecast_time,
                    predicted_aqi=predicted_aqi,
                    model_version=MODEL_VERSION
                )

                db.add(forecast)

            saved += 1

        # Step 4: Commit all predictions
        db.commit()

        return result, saved

    except Exception:
        db.rollback()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--city", required=True)
    parser.add_argument("--hours", type=int, default=48)

    args = parser.parse_args()

    create_tables()
    db = SessionLocal()

    try:
        result, total = save_forecast(
            db,
            args.city,
            args.hours
        )

        print("City:", result["city"])
        print("Model:", result["model"])
        print("Predictions saved:", total)
        print("MAE:", result["mae"])
        print("RMSE:", result["rmse"])

    finally:
        db.close()
