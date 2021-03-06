from tornado import web
from tornado import ioloop
from tornado import gen

from lib.database.users import get_user_from_email
from lib.database.auth import pop_deauth_request
from lib.database.auth import create_deauth_request
from lib.database.auth import delete_user_data
from lib.email_sender import send_deauthorization

import uuid


class UserDeauth(web.RequestHandler):
    _ioloop = ioloop.IOLoop().instance()

    @web.asynchronous
    @gen.coroutine
    def get(self):
        if self.get_argument('email', None):
            # pull user from database
            user = yield get_user_from_email(
                self.get_argument('email', None))
            if user is not None:
                token = str(uuid.uuid1())
                self._ioloop.add_callback(create_deauth_request,
                                          id=token, user_id=user['id'])
                link = "{0}/deauth?token={1}".format(
                    self.application.settings['base_url'],
                    token
                )
                send_deauthorization(user['email'], user['name'], link)
            else:
                raise web.HTTPError(
                        404,
                        'User is either already deleted or not in DB')

        elif (self.get_argument('token', None)):
            # pop the request
            request = yield pop_deauth_request(
                    self.get_argument('token', None))
            if request is not None:
                self._ioloop.add_callback(
                    delete_user_data,
                    id=request['user_id']
                )
                return self.redirect("{0}/leave#final".format(
                    self.application.settings['base_url'])
                )
            else:
                raise web.HTTPError(
                        404,
                        'Not found.')

        else:
            # return error
            raise web.HTTPError(
                    400,
                    'Insufficient params.')
