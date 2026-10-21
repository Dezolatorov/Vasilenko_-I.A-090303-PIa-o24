"""Отдельный процесс-consumer асинхронных событий (Notification/Audit).

Демонстрирует асинхронное взаимодействие Service -> Broker -> Consumer:
loans-service публикует событие LoanCreated/LoanReturned в RabbitMQ
(или в файловую шину при локальном запуске без брокера), а этот
независимый процесс читает очередь и журналирует событие.
"""

import argparse
import json
import logging
import os
import threading
import time

syspath_patched = False


def patch_sys_path():
    global syspath_patched
    if syspath_patched:
        return
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for p in (root, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
        if p not in sys.path:
            sys.path.insert(0, p)
    syspath_patched = True


def main():
    patch_sys_path()
    from shared.event_bus import make_event_bus

    logging.basicConfig(level=logging.INFO, format="%(asctime)s event-consumer %(levelname)s %(message)s")
    logger = logging.getLogger("event-consumer")

    parser = argparse.ArgumentParser()
    parser.add_argument("--events-dir", default=os.environ.get("EVENTS_DIR", "./events"))
    parser.add_argument("--broker-url", default=os.environ.get("BROKER_URL"))
    parser.add_argument("--interval", type=float, default=0.3)
    parser.add_argument("--duration", type=float, default=0.0)
    args = parser.parse_args()

    bus = make_event_bus(args.events_dir, args.broker_url)
    transport = "RabbitMQ" if args.broker_url else f"каталог {args.events_dir}"
    logger.info("event-consumer слушает %s", transport)

    processed = set()

    def handle(event):
        key = event.get("id")
        if key in processed:
            return
        processed.add(key)
        if event.get("type") in ("LoanCreated", "LoanReturned"):
            payload = event.get("payload", {})
            logger.info(
                "получено событие %s: книга=%s читатель=%s",
                event.get("type"),
                payload.get("book_id"),
                payload.get("reader_id"),
            )
            print(json.dumps(
                {"event": event.get("type"), "loan": payload.get("id"), "book": payload.get("book_id")},
                ensure_ascii=False,
            ))

    if args.duration and args.duration > 0:
        stop_event = threading.Event()
        thread = threading.Thread(
            target=bus.consume_loop,
            kwargs={"handler": handle, "interval": args.interval, "stop_event": stop_event},
            daemon=True,
        )
        thread.start()
        time.sleep(args.duration)
        stop_event.set()
        thread.join(timeout=5)
        logger.info("event-consumer завершил работу")
        return

    bus.consume_loop(handle, interval=args.interval)


if __name__ == "__main__":
    main()
