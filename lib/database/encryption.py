from tornado import gen
import rethinkdb as r
import cryptohelper

from .connection import connection
from .utils import dump_cursor


@gen.coroutine
def create_showtime_keys(showid, passphrase=None):
    if passphrase is None:
        passphrase = cryptohelper.generate_passphrase()
    shares = cryptohelper.split_passphrase(passphrase)
    public_key, private_key = cryptohelper.create_keypair(passphrase)
    conn = yield connection()
    data = {
        'public_key': public_key,
        'private_key': private_key,
        'id': showid,
    }
    result = yield r.table('encryption_show').insert(data).run(conn)
    if not result['errors']:
        print(showid, shares)
        # email_sender.send_shares(show, shares)
        # TODO: this
        pass
    return result


@gen.coroutine
def create_user_keys(userid, showid):
    conn = yield connection()
    public_key, private_key = cryptohelper.create_keypair()
    show_publickey = yield get_show_publickey(showid)
    enc_priv_key = cryptohelper.encrypt_blob(show_publickey, private_key)
    data = {
        'public_key': public_key,
        'enc_private_key': enc_priv_key,
        'showid': showid,
        'id': userid
    }
    result = yield r.table('encryption_user').insert(data).run(conn)
    return result


@gen.coroutine
def get_show_publickey(showid):
    conn = yield connection()
    publickey = yield r.table('encryption_show'). \
        get(showid).get_field('public_key').run(conn)
    return cryptohelper.import_key(publickey)


@gen.coroutine
def get_show_privatekey(showid, passphrase=None):
    conn = yield connection()
    privatekey = yield r.table('encryption_show'). \
        get(showid).get_field('private_key').run(conn)
    return cryptohelper.import_key(privatekey, passphrase)


@gen.coroutine
def get_user_publickey(userid):
    conn = yield connection()
    publickey = yield r.table('encryption_user'). \
        get(userid).get_field('public_key').run(conn)
    return cryptohelper.import_key(publickey)


@gen.coroutine
def get_user_keypair_from_showid(showid):
    conn = yield connection()
    result = yield r.table('encryption_user').filter({
        "showid": showid,
    }).run(conn)
    result = yield dump_cursor(result)
    return result
