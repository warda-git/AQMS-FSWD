
import csv
import argparse
from datetime import datetime, timezone

from app.database import SessionLocal, create_tables
from app.models import City, AQIReading


def parse_date(value):
    date = datetime.fromisoformat(
        value.strip().replace("Z", "+00:00")
    )

    if date.tzinfo is None:
        raise ValueError("Date must include a timezone")

    return date.astimezone(timezone.utc)


def optional_number(value):
    if value is None or value.strip() == "":
        return None
    return float(value)


def import_aqi_data(csv_path):
    create_tables()
    db = SessionLocal()

    imported = 0
    skipped = 0
    seen = set()

    try:
        with open(csv_path, "r", encoding="utf-8-sig",
                  newline="") as file:

            reader = csv.DictReader(file)

            required = {"city", "recorded_at", "aqi"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(
                    "CSV needs city, recorded_at and aqi columns"
                )

            cities = {
                city.name.lower(): city
                for city in db.query(City).all()
            }

            for line_no, row in enumerate(reader, start=2):
                try:
                    city_name = row["city"].strip().lower()
                    city = cities.get(city_name)

                    if city is None:
                        raise ValueError(
                            f"Unknown city: {row['city']}"
                        )

                    recorded_at = parse_date(
                        row["recorded_at"]
                    )

                    aqi = float(row["aqi"])
                    if aqi < 0:
                        raise ValueError("AQI cannot be negative")

                    source = (
                        (row.get("source") or "").strip()
                        or "CSV_IMPORT"
                    )

                    key = (
                        city.id,
                        recorded_at,
                        source
                    )

                    if key in seen:
                        skipped += 1
                        continue

                    seen.add(key)

                    exists = db.query(AQIReading).filter_by(
                        city_id=city.id,
                        recorded_at=recorded_at,
                        source=source
                    ).first()

                    if exists:
                        skipped += 1
                        continue

                    reading = AQIReading(
                        city_id=city.id,
                        recorded_at=recorded_at,
                        aqi=aqi,
                        pm25=optional_number(
                            row.get("pm25")
                        ),
                        pm10=optional_number(
                            row.get("pm10")
                        ),
                        no2=optional_number(
                            row.get("no2")
                        ),
                        co=optional_number(
                            row.get("co")
                        ),
                        source=source
                    )

                    db.add(reading)
                    imported += 1

                except (ValueError, TypeError) as error:
                    raise ValueError(
                        f"CSV line {line_no}: {error}"
                    ) from error

        db.commit()
        print(f"Imported: {imported}")
        print(f"Skipped duplicates: {skipped}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()

    import_aqi_data(args.file)
