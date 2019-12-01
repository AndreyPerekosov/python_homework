from pymemcache.client import base
import logging
ATTEMPTS_OF_CONNECTIONS = 10
SERVER_CONFIG = ('localhost', 11211)


def connect(func):
    def wraper(*args):
        client = None
        for dummy_index in range(ATTEMPTS_OF_CONNECTIONS):
            try:
                client = base.Client(SERVER_CONFIG, connect_timeout=20, timeout=20)
                client.get('test')
            except Exception as e:
                logging.exception(f"{e}. Number of attemts: {dummy_index}")
            else:
                break
        return func(*args, client=client)
    return wraper


@connect
def cache_set(*args, client):
    try:
        client.set(*args)
    except Exception as e:
        logging.exception(e)
    finally:
        client.close()



@connect
def cache_get(*args, client):
    try:
        value = float(client.get(*args).decode('utf-8'))
        return value
    except Exception:
        return None
    finally:
        client.close()



@connect
def get(*args, client):
    try:
        value = client.get(*args)
        if value:
            return value.decode('utf-8')
        else:
            return None
    except Exception as e:
        logging.exception(e)
    finally:
        client.close()



@connect
def delete(*args, client):
    client.delete(*args)
    client.close()
