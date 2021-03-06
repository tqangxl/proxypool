import proxypool.proxy_server as proxy_server
from proxypool.config import host, port
import pytest
from multiprocessing import Process
import requests


@pytest.fixture
def api(db):
    db.put_list(['127.0.0.1:80', '127.0.0.1:443', '127.0.0.1:1080'])
    proxy_server.conn = db # replace with test db
    server = Process(target=proxy_server.server_run)
    server.start()
    yield 'http://{0}:{1}'.format(host, port)
    db.pop_list(3)
    server.terminate()

def test_server_get(db, api):
    proxies = ['127.0.0.1:80', '127.0.0.1:443', '127.0.0.1:1080']

    assert requests.get('{0}/get'.format(api)).text in proxies

    assert eval(requests.get('{0}/get/3'.format(api)).text).sort() == proxies.sort()

    assert eval(requests.get('{0}/get/10'.format(api)).text).sort() == proxies.sort()

    assert db.count == int(requests.get('{0}/count'.format(api)).text)

