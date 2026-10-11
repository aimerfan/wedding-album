import pytest

from tests.conftest import auth


@pytest.fixture
def setup(join, add_photo):
    """小慧上傳了一張照片，阿凱來看。回傳 (小慧的 token, 阿凱的 token, 照片 id)。"""
    hui_token, hui = join("小慧")
    kai_token, _ = join("阿凱")
    return hui_token, kai_token, add_photo(hui["id"])


def _photo(client, token, photo_id):
    return client.get(f"/api/photos/{photo_id}", headers=auth(token)).get_json()


# --- 按讚 -----------------------------------------------------------------


def test_like_and_unlike(client, setup):
    _, kai, photo_id = setup

    res = client.put(f"/api/photos/{photo_id}/like", headers=auth(kai))
    assert res.status_code == 200
    assert res.get_json()["likeCount"] == 1
    assert res.get_json()["likedByMe"] is True

    res = client.delete(f"/api/photos/{photo_id}/like", headers=auth(kai))
    assert res.get_json()["likeCount"] == 0
    assert res.get_json()["likedByMe"] is False


def test_like_twice_counts_once(client, setup):
    # 網路不穩重送、手指連點，都不會變成兩個讚
    _, kai, photo_id = setup

    client.put(f"/api/photos/{photo_id}/like", headers=auth(kai))
    res = client.put(f"/api/photos/{photo_id}/like", headers=auth(kai))

    assert res.get_json()["likeCount"] == 1


def test_unlike_without_like_is_fine(client, setup):
    _, kai, photo_id = setup
    res = client.delete(f"/api/photos/{photo_id}/like", headers=auth(kai))
    assert res.status_code == 200


def test_likes_are_public_liked_by_me_is_personal(client, setup):
    hui, kai, photo_id = setup
    client.put(f"/api/photos/{photo_id}/like", headers=auth(kai))

    seen_by_hui = _photo(client, hui, photo_id)

    assert seen_by_hui["likeCount"] == 1
    assert seen_by_hui["likedByMe"] is False


def test_like_counts_in_list(client, join, add_photo):
    token, me = join("小慧")
    _, other = join("阿凱")
    liked = add_photo(me["id"])
    add_photo(me["id"])
    client.put(f"/api/photos/{liked}/like", headers=auth(token))

    items = client.get("/api/photos", headers=auth(token)).get_json()["items"]

    by_id = {p["id"]: p for p in items}
    assert by_id[liked]["likeCount"] == 1 and by_id[liked]["likedByMe"] is True
    assert sum(p["likeCount"] for p in items) == 1


def test_like_missing_photo_is_404(client, setup):
    _, kai, _ = setup
    assert client.put("/api/photos/p_nope/like", headers=auth(kai)).status_code == 404


def test_like_requires_token(client, setup):
    _, _, photo_id = setup
    assert client.put(f"/api/photos/{photo_id}/like").status_code == 401


def test_likes_received_in_my_stats(client, setup, join):
    hui, kai, photo_id = setup
    third, _ = join("婷婷")
    client.put(f"/api/photos/{photo_id}/like", headers=auth(kai))
    client.put(f"/api/photos/{photo_id}/like", headers=auth(third))

    stats = client.get("/api/me", headers=auth(hui)).get_json()["stats"]

    assert stats["likesReceived"] == 2


# --- 收藏 -----------------------------------------------------------------


def test_favorite_and_list(client, setup, join, add_photo):
    _, kai, photo_id = setup
    other_photo = add_photo(join("婷婷")[1]["id"])

    res = client.put(f"/api/photos/{photo_id}/favorite", headers=auth(kai))
    assert res.get_json()["favoritedByMe"] is True

    favorites = client.get(
        "/api/photos", headers=auth(kai), query_string={"favorited": "true"}
    ).get_json()["items"]
    assert [p["id"] for p in favorites] == [photo_id]
    assert other_photo not in [p["id"] for p in favorites]


def test_favorites_are_private(client, setup):
    hui, kai, photo_id = setup
    client.put(f"/api/photos/{photo_id}/favorite", headers=auth(kai))

    # 小慧看不到阿凱收藏了什麼
    assert _photo(client, hui, photo_id)["favoritedByMe"] is False
    mine = client.get("/api/photos", headers=auth(hui), query_string={"favorited": "true"})
    assert mine.get_json()["items"] == []


def test_unfavorite(client, setup):
    _, kai, photo_id = setup
    client.put(f"/api/photos/{photo_id}/favorite", headers=auth(kai))

    res = client.delete(f"/api/photos/{photo_id}/favorite", headers=auth(kai))

    assert res.get_json()["favoritedByMe"] is False
    assert client.get("/api/me", headers=auth(kai)).get_json()["stats"]["favorited"] == 0
