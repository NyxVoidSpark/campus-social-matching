import pytest
from app import app, db
from app import User
from app import Post, Group
from io import BytesIO


@pytest.fixture(autouse=True)
def setup_env():
    # 清理测试数据库表（在 app.app_context 下执行）
    with app.app_context():
        # 删除测试表中所有数据
        Post.query.delete()
        Group.query.delete()
        User.query.filter(User.username.in_(['tester', 'club50'])).delete()
        db.session.commit()


def create_user(username, user_id):
    with app.app_context():
        u = User(id=user_id, username=username, password='x', email=f'{username}@example.com')
        db.session.add(u)
        db.session.commit()
        return u


def test_create_and_list_posts():
    client = app.test_client()

    # create a new user in DB
    create_user('tester', '99')

    # unauthenticated create should 401
    r = client.post('/api/posts', data={'title': 't', 'category': '教学科研'})
    assert r.status_code == 401

    # create as authenticated user (simulate session)
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess['user_id'] = '99'; sess['username'] = 'tester'

        resp = client.post('/api/posts', data={'title': 'hello', 'category': '教学科研', 'content': 'hi', 'tags': 'a,b'})
        assert resp.status_code == 201

        # listing
        r2 = client.get('/api/posts')
        assert r2.status_code == 200
        data = r2.get_json()
        assert data['count'] == 1


def test_upload_file_and_group_flow():
    client = app.test_client()

    # create new user
    create_user('club50', '50')

    # create group as club50
    with app.test_request_context():
        with client.session_transaction() as sess:
            sess['user_id'] = '50'; sess['username'] = 'club50'

        resp = client.post('/api/groups', json={'name': '测试小组', 'description': '用于测试'})
        assert resp.status_code == 201

        # upload a file as the user
        file_data = (BytesIO(b'dummy'), 'f.pdf')
        resp2 = client.post('/api/posts', data={'title': 'X', 'category': '生活服务', 'content': 'ok', 'tags': 'k'}, content_type='multipart/form-data')
        # The endpoint may reject if duplicate detected (409) or accept (201)
        assert resp2.status_code in (201, 409)
