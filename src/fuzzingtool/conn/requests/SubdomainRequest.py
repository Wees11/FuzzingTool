## FuzzingTool
# 
# Authors:
#    Vitor Oriel C N Borges <https://github.com/VitorOriel>
# License: MIT (LICENSE.md)
#    Copyright (c) 2021 Vitor Oriel
#    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
## https://github.com/NESCAU-UFLA/FuzzingTool

from .Request import Request
from ..responses.Response import Response
from ...parsers.RequestParser import getHost, requestParser as parser
from ...exceptions.RequestExceptions import RequestException, InvalidHostname

import socket

class SubdomainRequest(Request):
    """Class that handle with the requests for subdomain fuzzing"""
    def __init__(self,
        url: str,
        method: str = 'GET',
        methods: list = [],
        data: dict = {},
        headers: dict = {},
        followRedirects: bool = True,
        proxy: dict = {},
        proxies: list = [],
    ):
        """Class constructor

        @type url: str
        @param url: The target URL
        @type method: str
        @param method: The request http verb (method)
        @type methods: list
        @param methods: The request methods list
        @type data: dict
        @param data: The parameters of the request, with default values if are given
        @type headers: dict
        @param headers: The HTTP header of the request
        @type followRedirects: bool
        @param followRedirects: The follow redirects flag
        @type proxy: dict
        @param proxy: The proxy used in the request
        @type proxies: list
        @param proxies: The list with the proxies used in the requests
        """
        super().__init__(
            url, method, methods, data,
            headers, followRedirects, proxy, proxies,
        )
    
    def resetRequestIndex(self):
        self._requestIndex = 0

    def resolveHostname(self, hostname: str):
        """Resolve the ip for the given hostname

        @type hostname: str
        @param hostname: The hostname of the target
        @returns str: The target IP
        """
        try:
            return socket.gethostbyname(hostname)
        except:
            self._requestIndex += 1
            raise InvalidHostname(f"Can't resolve hostname {hostname}")

    def request(self, payload: str):
        parser.setPayload(payload)
        ip = self.resolveHostname(getHost(parser.getUrl(self._url)))
        response = super().request(payload)
        response.custom['IP'] = ip
        return response