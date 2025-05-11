"""Module for score test"""
from src import scoring, store


def test_get_score(mocker):
    """test for score"""
    s = store.Store()
    mocker.patch("src.store.Store.cache_get", return_value=None)
    mocker.patch("src.store.Store.cache_set")
    assert scoring.get_score(store=s) == 0
    assert scoring.get_score(store=s, phone="1") == 1.5
    assert scoring.get_score(store=s, email="1") == 1.5
    assert scoring.get_score(store=s, gender="1") == 0
    assert scoring.get_score(store=s, first_name="1", last_name="1") == 0.5
    assert scoring.get_score(store=s, phone="1", first_name="1", last_name="1") == 2


def test_get_interests(mocker):
    """test for interests"""
    all_interests = [
        "cars",
        "pets",
        "travel",
        "hi-tech",
        "sport",
        "music",
        "books",
        "tv",
        "cinema",
        "geek",
        "otus",
    ]
    s = store.Store()
    mocker.patch("src.store.Store.get", return_value='["sport","music"]')
    client_interests = scoring.get_interests(store=s, cid=5)
    assert len(client_interests) == 2
    for interest in client_interests:
        assert interest in all_interests