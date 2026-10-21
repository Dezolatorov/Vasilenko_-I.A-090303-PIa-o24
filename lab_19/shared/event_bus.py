"""Файловая шина событий - упрощённый брокер сообщений.

Методичка требует асинхронное взаимодействие через брокер (Kafka/RabbitMQ),
однако в учебной среде отсутствуют Docker и брокеры. Честная замена:
событие сериализуется в JSON и дописывается в каталог outbox, а сервис-получатель
периодически сканирует этот каталог (polling). Это соответствует паттерну
Transactional Outbox: публикация события отделена от бизнес-транзакции и
не нарушает её атомарность.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid


class FileEventBus:
    def __init__(self, events_dir: str):
        self._events_dir = events_dir
        os.makedirs(events_dir, exist_ok=True)
        self._lock = threading.Lock()

    def publish(self, event_type: str, payload: dict) -> dict:
        """Создать и 'отправить' событие (запись в outbox-каталог)."""
        event = {
            "id": uuid.uuid4().hex,
            "type": event_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "payload": payload,
        }
        path = os.path.join(self._events_dir, f"{event['id']}.json")
        with self._lock:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(event, fh, ensure_ascii=False, indent=2)
        return event

    def poll(self, since_event_id: str | None = None) -> list[dict]:
        """Сообщения, появившиеся позже заданного события (для получателя)."""
        with self._lock:
            files = sorted(os.listdir(self._events_dir))
        events = []
        for name in files:
            if not name.endswith(".json"):
                continue
            with open(os.path.join(self._events_dir, name), "r", encoding="utf-8") as fh:
                event = json.load(fh)
            if since_event_id is None or event["id"] > since_event_id:
                events.append(event)
        return events

    def consume_loop(self, handler, since_event_id: str | None = None, interval: float = 0.5, stop_event=None) -> None:
        """Фоновая логика 'consumera' событий (polling каждые interval секунд)."""
        last_id = since_event_id
        while stop_event is None or not stop_event.is_set():
            for event in self.poll(last_id):
                try:
                    handler(event)
                except Exception as exc:  # noqa: BLE001
                    print(f"[event-bus] ошибка обработки события {event.get('id')}: {exc}")
                last_id = event["id"]
            if stop_event is not None:
                time.sleep(interval)


class RabbitEventBus:
    """Шина событий через RabbitMQ: Service → Broker → Consumer."""

    def __init__(self, url: str, queue: str = "library.events") -> None:
        self._url = url
        self._queue = queue

    def _connection(self):
        import pika

        return pika.BlockingConnection(pika.URLParameters(self._url))

    def publish(self, event_type: str, payload: dict) -> dict:
        import pika

        event = {
            "id": uuid.uuid4().hex,
            "type": event_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "payload": payload,
        }
        connection = self._connection()
        try:
            channel = connection.channel()
            channel.queue_declare(queue=self._queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=self._queue,
                body=json.dumps(event, ensure_ascii=False).encode("utf-8"),
                properties=pika.BasicProperties(delivery_mode=2),
            )
        finally:
            connection.close()
        return event

    def poll(self, since_event_id: str | None = None) -> list[dict]:
        """У RabbitMQ нет polling-выборки; события доставляет consume_loop."""
        return []

    def consume_loop(self, handler, since_event_id: str | None = None, interval: float = 0.5, stop_event=None) -> None:
        connection = self._connection()
        channel = connection.channel()
        channel.queue_declare(queue=self._queue, durable=True)
        channel.basic_qos(prefetch_count=1)

        def on_message(ch, method, _properties, body):
            event = json.loads(body.decode("utf-8"))
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001
                print(f"[rabbit] ошибка обработки события {event.get('id')}: {exc}")
            finally:
                ch.basic_ack(method.delivery_tag)

        channel.basic_consume(
            queue=self._queue,
            on_message_callback=on_message,
        )
        try:
            while stop_event is None or not stop_event.is_set():
                connection.process_data_events(time_limit=interval)
        finally:
            connection.close()


def make_event_bus(events_dir: str, broker_url: str | None = None):
    """RabbitMQ при наличии BROKER_URL, иначе файловая шина для локального запуска."""
    if broker_url:
        return RabbitEventBus(broker_url)
    return FileEventBus(events_dir)
