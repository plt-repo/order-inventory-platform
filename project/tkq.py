import taskiq_fastapi
from taskiq import InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_aio_pika import AioPikaBroker

from project.settings import settings

broker = AioPikaBroker(str(settings.rabbit_url))

if settings.environment.lower() == "pytest":
    broker = InMemoryBroker()


scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)

taskiq_fastapi.init(
    broker,
    "project.web.application:get_app",
)
