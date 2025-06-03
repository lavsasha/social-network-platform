from sqlalchemy import create_engine
from clickhouse_sqlalchemy import make_session
from clickhouse_models import Event, PostStats, PostDailyStats, UserStats


def init_clickhouse_tables():
    url = "clickhouse://default:password@clickhouse:8123/default"
    engine = create_engine(url)
    session = make_session(engine)

    try:
        print("Connecting to ClickHouse...")
        for model in [Event, PostStats, PostDailyStats, UserStats]:
            print(f"Creating table: {model.__tablename__}")
            model.__table__.create(bind=engine, checkfirst=True)

        print("All ClickHouse tables created successfully.")
    except Exception as e:
        print(f"Error creating ClickHouse tables: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_clickhouse_tables()
