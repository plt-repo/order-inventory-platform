from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from project.db.dependencies import get_db_session
from project.tkq import broker


@broker.task(schedule=[{"cron": "*/1 * * * *"}])
async def test_task(session: AsyncSession = TaskiqDepends(get_db_session)):
    print('hello from test_task')
