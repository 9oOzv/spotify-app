from requests import post, get
from typing import Iterable
from urllib.parse import urlencode
import webbrowser
from util import b64
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from log import (
    trace_func,
    trace_args,
    get_logger
)
from typing import Callable

log = get_logger('spotify-helper')


class SpotifyAPI:

    api_url: str = 'https://api.spotify.com/v1'
    client_id: str | None = None
    client_secret: str | None = None
    token: str | None = None
    code: str | None = None

    @trace_args(log)
    def __init__(
        self,
        client_id: str,
        client_secret: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret

    def _listen_for_code(self):
        log.debug('Listening for code')
        self.code = None
        _self = self

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = parse_qs(urlparse(self.path).query)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<script>window.close()</script>')
                self.server.query = query
                _self.code = query.get('code')[0]

        server = HTTPServer(
            ('localhost', 8000,),
            RequestHandler
        )
        server.handle_request()
        if not self.code:
            raise Exception('Authorization failed')
        return

    def _open_browser(
        self,
        url: str,
        params: dict,
    ):
        log.debug({
            'message': 'Opening browser',
            'url': url,
            'params': params
        })
        log.info('Opening browser')
        webbrowser.open(f'{url}?{urlencode(params)}')

    def authorize(self):
        url = 'https://accounts.spotify.com/authorize'
        query = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:8000/callback',
            'scope': 'user-library-read',
        }
        log.debug({
            'msg': 'Authorizing',
            'url': url,
            'query': query
        })
        self._open_browser(url, query)
        self._listen_for_code()
        return

    def refresh_token(self):
        self.authorize()
        data = {
            'grant_type': 'authorization_code',
            'code': self.code,
            'redirect_uri': 'http://localhost:8000/callback',
        }
        id = self.client_id
        secret = self.client_secret
        headers = {
            'Authorization': f'Basic {b64(f"{id}:{secret}")}'
        }
        log.debug({
            'message': 'Refreshing token',
            'data': data,
            'headers': headers
        })
        response = post(
            'https://accounts.spotify.com/api/token',
            headers=headers,
            data=data
        )
        response.raise_for_status()
        self.token = response.json()['access_token']

    @trace_func(log)
    def request(
        self,
        endpoint: str,
        param: str = '',
        query: dict = {},
        tries: int = 2,
        parser: Callable = lambda v: v.get('items', [])
    ) -> dict:
        if self.token is None:
            self.refresh_token()
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = get(
            f'{self.api_url}/{endpoint}/{param}',
            headers=headers,
            params=query
        )
        if response.status_code == 403 and tries > 0:
            self.refresh_token()
            return self.request(endpoint, param, query, tries - 1)
        if response.status_code != 200 and tries > 0:
            return self.request(endpoint, param, query, tries - 1)
        if response.status_code != 200:
            raise Exception(response.json())
        return parser(response.json())

    @trace_func(log)
    def request_paginated(
        self,
        endpoint: str,
        param: str = '',
        query: dict = {},
        limit: int = 50,
        start: int = 0,
        tries: int = 2,
        max_pages: int = 20,
        parser: Callable = lambda v: v.get('items', [])
    ) -> Iterable[dict]:
        offset = start
        while True:
            res = self.request(
                endpoint,
                param,
                {
                    **query,
                    'limit': limit,
                    'offset': offset,
                },
                tries,
                parser=parser
            )
            if not res:
                return
            yield from res
            offset += limit
            if offset / limit >= max_pages:
                return
