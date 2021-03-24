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

from ..default.DataScanner import DataScanner
from ....conn.Response import Response
from ....IO.OutputHandler import getFormatedResult, Colors

import html

class ReflectedScanner(DataScanner):
    __name__ = "Reflected Scanner"
    __author__ = "Vitor Oriel C N Borges"
    __desc__ = "Lookup if the payload was reflected in the response content"

    def __init__(self):
        super().__init__()
        self.__escaped = {}

    def getResult(self, response: Response):
        return super().getResult(response)

    def scan(self, result: dict):
        self.__escaped[result['Request']] = False
        if super().scan(result):
            reflected = result['Payload'] in result['Body']
            if not reflected:
                self.__escaped[result['Request']] = result['Payload'] in html.unescape(result['Body'])
            return reflected
        return False
    
    def getMessage(self, result: dict):
        escaped = ''
        if self.__escaped:
            if self.__escaped[result['Request']]:
                escaped = f" | {Colors.LIGHT_YELLOW}Reflected with HTML entities escaping"
            del self.__escaped[result['Request']]
        result = getFormatedResult(result)
        return (
            f"{result['Payload']} {Colors.GRAY}["+
            f"{Colors.LIGHT_GRAY}RTT{Colors.RESET} {result['Time Taken']} | "+
            f"{Colors.LIGHT_GRAY}Code{Colors.RESET} {result['Status']} | "+
            f"{Colors.LIGHT_GRAY}Size{Colors.RESET} {result['Length']} | "+
            f"{Colors.LIGHT_GRAY}Words{Colors.RESET} {result['Words']} | "+
            f"{Colors.LIGHT_GRAY}Lines{Colors.RESET} {result['Lines']}"+
            f"{escaped}{Colors.GRAY}]{Colors.RESET}"
        )