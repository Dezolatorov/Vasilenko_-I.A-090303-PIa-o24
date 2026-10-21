#!/usr/bin/env python3
"""Генерирует PNG-диаграмму архитектуры микросервисов для отчёта PDF."""

from PIL import Image, ImageDraw, ImageFont

W, H = 900, 720
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    title_f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
except Exception:
    font = ImageFont.load_default()
    small = font
    title_f = font

ACCENT = "#0066aa"
BAND = "#e8f0f8"
INK = "#1c1c1c"
RULE = "#888888"


def box(x, y, w, h, text, sub="", fill=BAND, border=ACCENT):
    d.rectangle([x, y, x + w, y + h], fill=fill, outline=border, width=2)
    d.text((x + w / 2, y + h / 2 - 12), text, font=title_f, fill=INK, anchor="mm")
    if sub:
        d.text((x + w / 2, y + h / 2 + 12), sub, font=small, fill=RULE, anchor="mm")


def arrow(x1, y1, x2, y2):
    d.line([x1, y1, x2, y2], fill=INK, width=2)
    # стрелка
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L, S = 12, 6
    p1 = (x2 - L * math.cos(ang - 0.4), y2 - L * math.sin(ang - 0.4))
    p2 = (x2 - L * math.cos(ang + 0.4), y2 - L * math.sin(ang + 0.4))
    d.line([(x2, y2), p1], fill=INK, width=2)
    d.line([(x2, y2), p2], fill=INK, width=2)


d.text((W / 2, 28), "Архитектура микросервисов «Библиотека» (вариант 2)", font=title_f, fill=ACCENT, anchor="mm")

# Client
box(330, 60, 240, 55, "Client", "API-запросы")
arrow(450, 115, 450, 160)

# Gateway
box(300, 160, 300, 60, "API Gateway", ":8000")
arrow(450, 220, 200, 270)
arrow(450, 220, 450, 270)
arrow(450, 220, 700, 270)

# Services
box(110, 270, 180, 90, "readers", "Service  :8001")
box(360, 270, 180, 90, "books", "Service  :8002")
box(610, 270, 180, 90, "loans", "Service  :8003")

# DBs
box(110, 420, 180, 60, "readers.json", "БД читателей")
box(360, 420, 180, 60, "books.json", "БД книг")
box(610, 420, 180, 60, "loans.json", "БД выдач")

arrow(200, 360, 200, 420)
arrow(450, 360, 450, 420)
arrow(700, 360, 700, 420)

# events from loans
d.text((790, 380), "LoanCreated", font=small, fill=INK)
arrow(790, 420, 790, 520)
box(650, 520, 200, 70, "Файловая шина", "data/events/ (outbox)")
arrow(750, 590, 660, 640)
box(560, 640, 200, 60, "event-consumer", "Notification/Audit")

# label of inter-service sync
d.text((285, 505), "loans -> readers/books (HTTP/REST)", font=small, fill=RULE)

img.save(r"C:\Users\Игорь\Documents\MultiTool\HomeChats\Chat\lab19-report-data\architecture.png")
print("saved architecture.png")