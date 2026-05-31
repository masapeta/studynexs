import asyncio
import asyncpg
from app.core.config import get_settings

async def create_test_db():
    settings = get_settings()
    # Connect to default postgres DB to create the new one
    conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database="postgres"
    )
    try:
        await conn.execute("CREATE DATABASE studynexs_test")
        print("Database studynexs_test created successfully.")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("Database studynexs_test already exists.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_db())
