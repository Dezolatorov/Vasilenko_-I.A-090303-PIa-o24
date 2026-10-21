# Отчёт по CDN-эксперименту

Origin: http://127.0.0.1:8001/ (Cache-Control: no-store)
CDN: http://127.0.0.1:8002/ (Cache-Control: public, max-age=60)

| Источник | Ресурс | Попытка | Код | Размер, байт | Время, мс | Cache-Control | Age | X-Cache |
|---|---|---|---|---|---|---|---|---|
| origin | images/cover-1.jpg | 1 | 200 | 161897 | 19.11 | no-store | — | BYPASS |
| cdn | images/cover-1.jpg | 1 | 200 | 161897 | 2.22 | public, max-age=60 | 0 | MISS |
| origin | images/cover-1.jpg | 2 | 200 | 161897 | 2.56 | no-store | — | BYPASS |
| cdn | images/cover-1.jpg | 2 | 200 | 161897 | 1.55 | public, max-age=60 | 1 | HIT |
| origin | css/style.css | 1 | 200 | 1499 | 1.92 | no-store | — | BYPASS |
| cdn | css/style.css | 1 | 200 | 1499 | 2.16 | public, max-age=60 | 0 | MISS |
| origin | css/style.css | 2 | 200 | 1499 | 1.9 | no-store | — | BYPASS |
| cdn | css/style.css | 2 | 200 | 1499 | 1.36 | public, max-age=60 | 1 | HIT |
| origin | js/app.js | 1 | 200 | 2775 | 1.36 | no-store | — | BYPASS |
| cdn | js/app.js | 1 | 200 | 2775 | 1.25 | public, max-age=60 | 0 | MISS |
| origin | js/app.js | 2 | 200 | 2775 | 2.04 | no-store | — | BYPASS |
| cdn | js/app.js | 2 | 200 | 2775 | 1.26 | public, max-age=60 | 1 | HIT |

## Итоги

Среднее время (origin, 1-й запрос): 7.46 мс
Среднее время (cdn, 1-й запрос): 1.88 мс
Среднее время (cdn, 2-й запрос): 1.39 мс
