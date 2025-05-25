from sqlalchemy import create_engine
from clickhouse_sqlalchemy import make_session
from clickhouse_models import Event, PostStats, PostDailyStats, UserStats


def init_clickhouse_tables():
    url = "clickhouse://default:password@clickhouse:8123/default"
    engine = create_engine(url)
    session = make_session(engine)

    try:
        print("Подключение к ClickHouse...")
        for model in [Event, PostStats, PostDailyStats, UserStats]:
            print(f"Создание таблицы: {model.__tablename__}")
            model.__table__.create(bind=engine, checkfirst=True)

        print("Все таблицы ClickHouse успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании таблиц ClickHouse: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_clickhouse_tables()
