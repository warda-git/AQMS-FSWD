
import argparse
import csv
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.database import SessionLocal
from app.forecasting import forecast_aqi


def save_forecast_outputs(result, output_dir="results"):
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    city = result["city"]
    hours = len(result["forecast"])

    # Convert timestamps and predictions
    dates = [
        datetime.fromisoformat(row["forecast_for"])
        for row in result["forecast"]
    ]

    values = [
        row["predicted_aqi"]
        for row in result["forecast"]
    ]

    # Save predictions to CSV
    csv_path = folder / "forecast.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["forecast_for", "predicted_aqi"])

        for row in result["forecast"]:
            writer.writerow([
                row["forecast_for"],
                row["predicted_aqi"]
            ])

    # Create forecast graph
    plt.figure(figsize=(11, 5))

    plt.plot(
        dates,
        values,
        marker="o",
        markersize=3,
        label="Predicted AQI"
    )

    plt.title(f"{city} - {hours} Hour AQI Forecast")
    plt.xlabel("Forecast Date and Time")
    plt.ylabel("Predicted AQI")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()

    graph_path = folder / "forecast.png"

    plt.savefig(graph_path, dpi=150)
    plt.close()

    print("Forecast CSV:", csv_path)
    print("Forecast graph:", graph_path)

    print("Model:", result["model"])
    print("MAE:", result["mae"])
    print("RMSE:", result["rmse"])

    return csv_path, graph_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    parser.add_argument("--hours", type=int, default=48)
    args = parser.parse_args()

    db = SessionLocal()

    try:
        result = forecast_aqi(
            db,
            city_name=args.city,
            hours=args.hours
        )

        save_forecast_outputs(result)

    finally:
        db.close()
