"""Adapt existing isolated UI fixtures to the short-session transport. No real API calls.

These suites model an already-saved browser session; real HttpOnly storage, rotation,
expiry and CSRF are separately exercised by the source auth and PostgreSQL gates.
"""
import inspect
import json

class _Route:
    def __init__(self, route):
        self._route = route

    def __getattr__(self, name):
        return getattr(self._route, name)

    def fulfill(self, **kwargs):
        origin = self.request.headers.get('origin')
        headers = dict(kwargs.pop('headers', {}) or {})
        if origin:
            headers.update({'access-control-allow-origin': origin,
                            'access-control-allow-credentials': 'true',
                            'access-control-allow-headers': 'authorization,content-type,x-giralab-player-id,x-giralab-csrf',
                            'access-control-allow-methods': 'GET,POST,OPTIONS'})
        return self._route.fulfill(headers=headers, **kwargs)

def _session_response(route):
    endpoint = route.request.url.split('/api/')[-1].split('?')[0]
    if route.request.method == 'OPTIONS':
        return {'status': 204, 'body': ''}
    if endpoint in ('auth/cookie-check', 'auth/bootstrap', 'auth/refresh', 'auth/reset'):
        return {'status': 200, 'content_type': 'application/json', 'body': json.dumps({'ok': True})}
    return None

def with_session_transport(handler):
    if inspect.iscoroutinefunction(handler):
        async def dispatch(route):
            route = _Route(route)
            response = _session_response(route)
            if response is not None:
                return await route.fulfill(**response)
            return await handler(route)
    else:
        def dispatch(route):
            route = _Route(route)
            response = _session_response(route)
            if response is not None:
                return route.fulfill(**response)
            return handler(route)
    return dispatch
