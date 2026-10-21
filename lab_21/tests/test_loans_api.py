"""API-С‚РµСЃС‚С‹ РІС‹РґР°С‡ Рё РІРѕР·РІСЂР°С‚РѕРІ РєРЅРёРі + Р±РёР·РЅРµСЃ-РїСЂР°РІРёР»Р° С‡РµСЂРµР· HTTP."""
from tests.conftest import admin_token, api_headers, register_and_token


def _user(client):
    return register_and_token(client, username="uzerloans", email="ul@test.ru")


def _admin(client, db):
    return admin_token(client, db)


def _author(client, token):
    r = client.post("/authors", headers=api_headers(token),
                    json={"name": "РђРІС‚РѕСЂ Р’С‹РґР°С‡"})
    return r.json()["id"]


def _books(client, token, a, n=3, copies=1):
    ids = []
    for i in range(n):
        r = client.post("/books", headers=api_headers(token),
                        json={"title": f"Р’Р«Р”РђР§Рђ{i}", "author_id": a,
                              "year": 2000, "total_copies": copies})
        ids.append(r.json()["id"])
    return ids


def test_issue_and_return_flow(client, db):
    ak = _admin(client, db)
    uk = _user(client)
    a = _author(client, ak)
    book = _books(client, ak, a, 1)[0]

    r = client.post("/loans", headers=api_headers(uk), json={"book_id": book})
    assert r.status_code == 201
    loan = r.json()
    assert loan["returned"] is False
    lid = loan["id"]

    r = client.get(f"/loans/{lid}", headers=api_headers(uk))
    assert r.status_code == 200

    r = client.post(f"/loans/{lid}/return", headers=api_headers(uk), json={})
    assert r.status_code == 200
    assert r.json()["returned"] is True


def test_issue_unavailable_book_conflict(client, db):
    ak = _admin(client, db)
    uk = _user(client)
    a = _author(client, ak)
    book = _books(client, ak, a, 1, copies=1)[0]

    # 1-СЏ РІС‹РґР°С‡Р° СѓСЃРїРµС€РЅР°, СЃРІРѕР±РѕРґРЅС‹С… РєРѕРїРёР№ Р±РѕР»СЊС€Рµ РЅРµС‚
    r = client.post("/loans", headers=api_headers(uk), json={"book_id": book})
    assert r.status_code == 201
    # 2-СЏ РІС‹РґР°С‡Р° С‚РѕР№ Р¶Рµ РєРЅРёРіРё - conflict (РЅРµС‚ СЃРІРѕР±РѕРґРЅС‹С… СЌРєР·РµРјРїР»СЏСЂРѕРІ)
    r = client.post("/loans", headers=api_headers(uk), json={"book_id": book})
    assert r.status_code == 409
    assert r.json()["error"] == "BUSINESS_RULE_VIOLATION"


def test_issue_missing_book_404(client, db):
    uk = _user(client)
    r = client.post("/loans", headers=api_headers(uk), json={"book_id": 99999})
    assert r.status_code == 404


def test_loan_limit_conflict(client, db):
    ak = _admin(client, db)
    uk = _user(client)
    a = _author(client, ak)
    # 5 РєРЅРёРі = Р»РёРјРёС‚ MAX_ACTIVE_LOANS
    books = _books(client, ak, a, 5, copies=1)
    for bid in books:
        r = client.post("/loans", headers=api_headers(uk), json={"book_id": bid})
        assert r.status_code == 201

    # 6-СЏ РєРЅРёРіР° РЅРµРґРѕСЃС‚СѓРїРЅР° РёР·-Р·Р° Р»РёРјРёС‚Р°
    extra = _books(client, ak, a, 1, copies=1)[0]
    r = client.post("/loans", headers=api_headers(uk), json={"book_id": extra})
    assert r.status_code == 409


def test_user_cannot_return_others_loan(client, db):
    ak = _admin(client, db)
    u1 = register_and_token(client, username="own1", email="o1@test.ru")
    u2 = register_and_token(client, username="own2", email="o2@test.ru")
    a = _author(client, ak)
    book = _books(client, ak, a, 1)[0]

    r = client.post("/loans", headers=api_headers(u1), json={"book_id": book})
    lid = r.json()["id"]

    # u2 (РЅРµ РІР»Р°РґРµР»РµС†) РїС‹С‚Р°РµС‚СЃСЏ РІРµСЂРЅСѓС‚СЊ С‡СѓР¶СѓСЋ РІС‹РґР°С‡Сѓ -> 403
    r = client.post(f"/loans/{lid}/return", headers=api_headers(u2), json={})
    assert r.status_code == 403


def test_list_loans_filter_returned(client, db):
    ak = _admin(client, db)
    uk = _user(client)
    a = _author(client, ak)
    b1, b2 = _books(client, ak, a, 2)

    client.post("/loans", headers=api_headers(uk), json={"book_id": b1})
    lo = client.post("/loans", headers=api_headers(uk), json={"book_id": b2}).json()
    client.post(f"/loans/{lo['id']}/return", headers=api_headers(uk), json={})

    r = client.get("/loans", params={"returned": "false"}, headers=api_headers(uk))
    active = r.json()
    assert len(active) == 1 and active[0]["book_id"] == b1

    r = client.get("/loans", params={"returned": "true"}, headers=api_headers(uk))
    done = r.json()
    assert len(done) == 1 and done[0]["book_id"] == b2