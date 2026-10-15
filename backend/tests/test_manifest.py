def test_manifest_puts_event_code_in_start_url(client):
    # iPhone 從主畫面打開時只有 start_url，活動碼要帶在裡面才加入得了相簿
    res = client.get("/api/manifest?code=test-code")

    assert res.status_code == 200
    assert res.mimetype == "application/manifest+json"
    body = res.get_json(force=True)
    assert body["start_url"] == "/?code=test-code"
    assert body["id"] == "/"
    assert body["scope"] == "/"
    assert all(icon["src"].startswith("/") for icon in body["icons"])


def test_manifest_ignores_wrong_event_code(client):
    # 錯的活動碼（例如管理員代碼）不放進去，不然主畫面打開後一樣加入不了
    for url in ("/api/manifest?code=nope", "/api/manifest"):
        body = client.get(url).get_json(force=True)
        assert body["start_url"] == "/"


def test_manifest_encodes_event_code(app, client):
    app.config["EVENT_CODE"] = "婚禮 &1"

    body = client.get("/api/manifest", query_string={"code": "婚禮 &1"}).get_json(force=True)

    assert body["start_url"] == "/?code=%E5%A9%9A%E7%A6%AE+%261"
