
from app.database import SessionLocal, create_tables
from app.models import Province, Region, City


# Initial locations for AQMS
locations = {
    "Punjab": {
        "Lahore Division": [
            ("Lahore", 31.5204, 74.3587)
        ],
        "Rawalpindi Division": [
            ("Rawalpindi", 33.5651, 73.0169),
            ("Attock", 33.7660, 72.3609)
        ],
        "Faisalabad Division": [
            ("Faisalabad", 31.4504, 73.1350)
        ]
    },
    "Sindh": {
        "Karachi Division": [
            ("Karachi", 24.8607, 67.0011)
        ]
    },
    "Khyber Pakhtunkhwa": {
        "Hazara Division": [
            ("Abbottabad", 34.1463, 73.2117),
            ("Mansehra", 34.3302, 73.1968)
        ]
    },
    "Islamabad Capital Territory": {
        "Islamabad": [
            ("Islamabad", 33.6844, 73.0479)
        ]
    }
}


def seed_database():
    create_tables()
    db = SessionLocal()

    try:
        for province_name, regions in locations.items():

            province = db.query(Province).filter_by(
                name=province_name
            ).first()

            if province is None:
                province = Province(name=province_name)
                db.add(province)
                db.flush()

            for region_name, cities in regions.items():

                region = db.query(Region).filter_by(
                    name=region_name,
                    province_id=province.id
                ).first()

                if region is None:
                    region = Region(
                        name=region_name,
                        province_id=province.id
                    )
                    db.add(region)
                    db.flush()

                for city_name, latitude, longitude in cities:

                    city = db.query(City).filter_by(
                        name=city_name,
                        region_id=region.id
                    ).first()

                    if city is None:
                        city = City(
                            name=city_name,
                            region_id=region.id,
                            latitude=latitude,
                            longitude=longitude
                        )
                        db.add(city)

        db.commit()
        print("Database seeded successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
