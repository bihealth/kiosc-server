"""Copy of ProxyView from ``django-revproxy`` that can be configured to not post empty bodies.

For license etc. see https://github.com/TracyWebTech/django-revproxy
"""

import re
import mimetypes
import logging

import urllib3

from django.utils.six.moves.urllib.parse import urlparse, urlencode, quote_plus

from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.views.generic import View
from django.utils.decorators import classonlymethod

from revproxy.exceptions import InvalidUpstream
from revproxy.utils import (
    normalize_request_headers,
    encode_items,
    cookie_from_string,
    should_stream,
    set_response_headers,
)

# Chars that don't need to be quoted. We use same than nginx:
#   https://github.com/nginx/nginx/blob/nginx-1.9/src/core/ngx_string.c
#   (Lines 1433-1449)
QUOTE_SAFE = r'<.;>\(}*+|~=-$/_:^@)[{]&\'!,"`'


ERRORS_MESSAGES = {
    "upstream-no-scheme": ("Upstream URL scheme must be either " "'http' or 'https' (%s).")
}


#: Default number of bytes that are going to be read in a file lecture
DEFAULT_AMT = 2 ** 16


logger = logging.getLogger("revproxy.response")


HTTP_POOLS = urllib3.PoolManager()


def get_django_response(proxy_response, strict_cookies=False):
    """This method is used to create an appropriate response based on the
    Content-Length of the proxy_response. If the content is bigger than
    MIN_STREAMING_LENGTH, which is found on utils.py,
    than django.http.StreamingHttpResponse will be created,
    else a django.http.HTTPResponse will be created instead

    :param proxy_response: An Instance of urllib3.response.HTTPResponse that
                           will create an appropriate response
    :param strict_cookies: Whether to only accept RFC-compliant cookies
    :returns: Returns an appropriate response based on the proxy_response
              content-length
    """
    status = proxy_response.status
    headers = proxy_response.headers

    logger.debug("Proxy response headers: %s", headers)

    content_type = headers.get("Content-Type")

    logger.debug("Content-Type: %s", content_type)

    if should_stream(proxy_response):
        logger.info("Content-Length is bigger than %s", DEFAULT_AMT)
        # The remaining isssue is that read() hangs here now.
        #  > /bioconda/2018-02/miniconda3/envs/kiosc/lib/python3.6/site-packages/urllib3/response.py(442)read()
        # Also this would hang here
        #  > proxy_response._original_response.fp.read()
        s = proxy_response.stream(DEFAULT_AMT)
        response = StreamingHttpResponse(s, status=status, content_type=content_type)
    else:
        content = proxy_response.data or b""
        response = HttpResponse(content, status=status, content_type=content_type)

    logger.info("Normalizing response headers")
    set_response_headers(response, headers)

    logger.debug("Response headers: %s", getattr(response, "_headers"))

    cookies = proxy_response.headers.getlist("set-cookie")
    logger.info("Checking for invalid cookies")
    for cookie_string in cookies:
        cookie_dict = cookie_from_string(cookie_string, strict_cookies=strict_cookies)
        # if cookie is invalid cookie_dict will be None
        if cookie_dict:
            response.set_cookie(**cookie_dict)

    logger.debug("Response cookies: %s", response.cookies)

    return response


class ProxyView(View):
    """View responsable by excute proxy requests, process and return
    their responses.
    """

    _upstream = None

    add_remote_user = False
    default_content_type = "application/octet-stream"
    retries = None
    rewrite = tuple()  # It will be overrided by a tuple inside tuple.
    strict_cookies = False
    #: Do not send any body if it is empty (put ``None`` into the ``urlopen()``
    #: call).  This is required when proxying to Shiny apps, for example.
    suppress_empty_body = False
    #: Whether or not to rescue the "upgrade" hop-by-hop headers for proxying
    #: of websocket.
    rescue_websocket_headers = False

    def __init__(self, *args, **kwargs):
        super(ProxyView, self).__init__(*args, **kwargs)

        self._rewrite = []
        # Take all elements inside tuple, and insert into _rewrite
        for from_pattern, to_pattern in self.rewrite:
            from_re = re.compile(from_pattern)
            self._rewrite.append((from_re, to_pattern))
        self.http = HTTP_POOLS
        self.log = logging.getLogger("revproxy.view")
        self.log.info("ProxyView created")

    @property
    def upstream(self):
        if not self._upstream:
            raise NotImplementedError("Upstream server must be set")
        return self._upstream

    @upstream.setter
    def upstream(self, value):
        self._upstream = value

    def get_upstream(self, path):
        upstream = self.upstream

        if not getattr(self, "_parsed_url", None):
            self._parsed_url = urlparse(upstream)

        if self._parsed_url.scheme not in ("http", "https"):
            raise InvalidUpstream(ERRORS_MESSAGES["upstream-no-scheme"] % upstream)

        if path and upstream[-1] != "/":
            upstream += "/"

        return upstream

    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super(ProxyView, cls).as_view(**initkwargs)
        view.csrf_exempt = True
        return view

    def _format_path_to_redirect(self, request):
        full_path = request.get_full_path()
        self.log.debug("Dispatch full path: %s", full_path)
        for from_re, to_pattern in self._rewrite:
            if from_re.match(full_path):
                redirect_to = from_re.sub(to_pattern, full_path)
                self.log.debug("Redirect to: %s", redirect_to)
                return redirect_to

    def get_proxy_request_headers(self, request):
        """Get normalized headers for the upstream
        Gets all headers from the original request and normalizes them.
        Normalization occurs by removing the prefix ``HTTP_`` and
        replacing and ``_`` by ``-``. Example: ``HTTP_ACCEPT_ENCODING``
        becames ``Accept-Encoding``.
        .. versionadded:: 0.9.1
        :param request:  The original HTTPRequest instance
        :returns:  Normalized headers for the upstream
        """
        return normalize_request_headers(request)

    def get_request_headers(self):
        """Return request headers that will be sent to upstream.
        The header REMOTE_USER is set to the current user
        if AuthenticationMiddleware is enabled and
        the view's add_remote_user property is True.
        .. versionadded:: 0.9.8
        """
        request_headers = self.get_proxy_request_headers(self.request)

        if self.add_remote_user and hasattr(self.request, "user") and self.request.user.is_active:
            request_headers["REMOTE_USER"] = self.request.user.get_username()
            self.log.info("REMOTE_USER set")

        return request_headers

    def get_quoted_path(self, path):
        """Return quoted path to be used in proxied request"""
        return quote_plus(path.encode("utf8"), QUOTE_SAFE)

    def get_encoded_query_params(self):
        """Return encoded query params to be used in proxied request"""
        get_data = encode_items(self.request.GET.lists())
        return urlencode(get_data)

    def _created_proxy_response(self, request, path):
        request_payload = request.body
        if self.suppress_empty_body and not request_payload:
            request_payload = None

        self.log.debug("Request headers: %s", self.request_headers)

        path = self.get_quoted_path(path)

        request_url = self.get_upstream(path) + path
        self.log.debug("Request URL: %s", request_url)

        if request.GET:
            request_url += "?" + self.get_encoded_query_params()
            self.log.debug("Request URL: %s", request_url)

        try:
            proxy_response = self.http.urlopen(
                request.method,
                request_url,
                redirect=False,
                retries=self.retries,
                headers=self.request_headers,
                body=request_payload,
                decode_content=False,
                preload_content=False,
            )
            self.log.debug("Proxy response header: %s", proxy_response.getheaders())
        except urllib3.exceptions.HTTPError as error:
            self.log.exception(error)
            raise

        return proxy_response

    def _replace_host_on_redirect_location(self, request, proxy_response):
        location = proxy_response.headers.get("Location")
        if location:
            if request.is_secure():
                scheme = "https://"
            else:
                scheme = "http://"
            request_host = scheme + request.get_host()

            upstream_host_http = "http://" + self._parsed_url.netloc
            upstream_host_https = "https://" + self._parsed_url.netloc

            location = location.replace(upstream_host_http, request_host)
            location = location.replace(upstream_host_https, request_host)
            proxy_response.headers["Location"] = location
            self.log.debug("Proxy response LOCATION: %s", proxy_response.headers["Location"])

    def _set_content_type(self, request, proxy_response):
        content_type = proxy_response.headers.get("Content-Type")
        if not content_type:
            content_type = mimetypes.guess_type(request.path)[0] or self.default_content_type
            proxy_response.headers["Content-Type"] = content_type
            self.log.debug(
                "Proxy response CONTENT-TYPE: %s", proxy_response.headers["Content-Type"]
            )

    def dispatch(self, request, path):
        self.request_headers = self.get_request_headers()

        redirect_to = self._format_path_to_redirect(request)
        if redirect_to:
            return redirect(redirect_to)

        proxy_response = self._created_proxy_response(request, path)

        self._replace_host_on_redirect_location(request, proxy_response)
        self._set_content_type(request, proxy_response)

        response = get_django_response(proxy_response, strict_cookies=self.strict_cookies)
        # Rescue hop-by-hop headers
        if self.rescue_websocket_headers and "socket" in path:
            for key, value in proxy_response.headers.items():
                if "upgrade" in key.lower() or "upgrade" in value.lower():
                    response[key] = value

        self.log.debug("RESPONSE RETURNED: %s", response)
        return response
