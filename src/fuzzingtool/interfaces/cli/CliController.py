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

from .CliArgumentParser import *
from .CliOutput import cliOutput as co
from ..ArgumentBuilder import ArgumentBuilder as AB
from ... import version
from ...utils.FileHandler import fileHandler as fh
from ...core import *
from ...conn import *
from ...factories.HttpFactory import HttpFactory
from ...factories.DictFactory import DictFactory
from ...exceptions.MainExceptions import SkipTargetException
from ...exceptions.RequestExceptions import InvalidHostname, RequestException

from queue import Queue
import time
import threading

def banner():
    """Gets the program banner

    @returns str: The program banner
    """
    banner = ("\033[36m   ____                        _____       _\n"+
              "\033[36m  |  __|_ _ ___ ___ _ ___ ___ |_   _|_ ___| |"+f"\033[0m Version {version()}\n"+
              "\033[36m  |  __| | |- _|- _|'|   | . |  | | . | . | |\n"+
              "\033[36m  |_|  |___|___|___|_|_|_|_  |  |_|___|___|_|\n"+
              "\033[36m                         |___|\033[0m\n\n"+
              "  [!] Disclaimer: We're not responsible for the misuse of this tool.\n"+
              "      This project was created for educational purposes\n"+
              "      and should not be used in environments without legal authorization.\n")
    return banner

class CliController:
    """Class that handle with the entire application

    Attributes:
        requesters: The requesters list
        startedTime: The time when start the fuzzing test
        allResults: The results dictionary for each host
        lock: A thread locker to prevent overwrites on logfiles
        blacklistStatus: The blacklist status object
    """
    def __init__(self):
        self.requesters = []
        self.startedTime = 0
        self.allResults = {}
        self.lock = threading.Lock()
        self.blacklistStatus = None

    def isVerboseMode(self):
        """The verboseMode getter

        @returns bool: The verbose mode flag
        """
        return self.verbose[0]

    def main(self):
        """The main function.
           Prepares the application environment and starts the fuzzing
        """
        try:
            self.init()
            self.checkConnectionAndRedirections()
        except KeyboardInterrupt:
            co.abortBox("Test aborted by the user")
            exit(0)
        except Exception as e:
            co.errorBox(str(e))
        self.start()

    def init(self):
        """The initialization function.
           Set the application variables including plugins requires
        """
        parser = CliArgumentParser()
        co.print(banner())
        self.__initRequesters(parser)
        self.globalScanner = parser.scanner
        self.matcher = Matcher.fromString(
            parser.matchStatus,
            parser.matchLength,
            parser.matchTime
        )
        self.verbose = parser.verbose
        co.setVerbosityOutput(self.isVerboseMode())
        if parser.blacklistedStatus:
            blacklistedStatus = parser.blacklistedStatus
            action = parser.blacklistAction
            self.blacklistStatus = BlacklistStatus(
                status=blacklistedStatus,
                action=action,
                actionParam=parser.blacklistActionParam,
                actionCallbacks={
                    'skip': self._skipCallback,
                    'wait': self._waitCallback,
                },
            )
            co.infoBox(f"Blacklisted status codes: {blacklistedStatus} with action {action}")
        self.delay = parser.delay
        self.numberOfThreads = parser.numberOfThreads
        if self.globalScanner:
            self.globalScanner.updateMatcher(self.matcher)
            self.scanner = self.globalScanner
            co.setMessageCallback(self.scanner.cliCallback)
        self.__initDictionary(parser)

    def checkConnectionAndRedirections(self):
        """Test the connection to target.
           If data fuzzing is detected, check for redirections
        """
        for requester in self.requesters:
            co.infoBox(f"Validating {requester.getUrl()} ...")
            co.infoBox("Testing connection ...")
            try:
                requester.testConnection()
            except RequestException as e:
                if not co.askYesNo('warning', f"{str(e)}. Continue anyway?"):
                    co.infoBox(f"Target removed from list.")
                    self.requesters.remove(requester)
            else:
                co.infoBox("Connection status: OK")
                if requester.isDataFuzzing():
                    self.checkRedirections(requester)
        if len(self.requesters) == 0:
            raise Exception("No targets left for fuzzing")

    def checkRedirections(self, requester: Request):
        """Check the redirections for a target.
           Perform a redirection check for each method in requester methods list
        
        @type requester: Request
        @param requester: The requester for the target
        """
        co.infoBox("Testing redirections ...")
        for method in requester.methods:
            requester.setMethod(method)
            co.infoBox(f"Testing with {method} method ...")
            try:
                if requester.hasRedirection():
                    if co.askYesNo('warning', "You was redirected to another page. Remove this method?"):
                        requester.methods.remove(method)
                        co.infoBox(f"Method {method} removed from list")
                else:
                    co.infoBox("No redirections")
            except RequestException as e:
                co.warningBox(f"{str(e)}. Removing method {method}")
        if len(requester.methods) == 0:
            self.requesters.remove(requester)
            co.warningBox("No methods left on this target, removed from targets list")

    def start(self):
        """Starts the fuzzing application.
           Each target is fuzzed based on their own methods list
        """
        self.startedTime = time.time()
        self.fuzzer = None
        try:
            for requester in self.requesters:
                try:
                    self.prepareTarget(requester)
                    co.infoBox(f"Starting test on '{self.requester.getUrl()}' ...")
                    for method in self.requester.methods:
                        self.requester.resetRequestIndex()
                        self.requester.setMethod(method)
                        co.infoBox(f"Set method for fuzzing: {method}")
                        self.prepareFuzzer()
                        if not self.isVerboseMode():
                            co.print("")
                except SkipTargetException as e:
                    if self.fuzzer and self.fuzzer.isRunning():
                        if not self.isVerboseMode():
                            co.print("")
                        co.warningBox("Skip target detected, stopping threads ...")
                        self.fuzzer.stop()
                    co.abortBox(f"{str(e)}. Target skipped")
        except KeyboardInterrupt:
            if self.fuzzer and self.fuzzer.isRunning():
                co.abortBox("Test aborted, stopping threads ...")
                self.fuzzer.stop()
            co.abortBox("Test aborted by the user")
        finally:
            self.showFooter()
            co.infoBox("Test completed")

    def prepareTarget(self, requester: Request):
        """Prepare the target variables for the fuzzing tests.
           Both error logger and default scanners are setted
        
        @type requester: Request
        @param requester: The requester for the target
        """
        self.requester = requester
        targetHost = getHost(getPureUrl(requester.getUrlDict()))
        co.infoBox(f"Preparing target {targetHost} ...")
        before = time.time()
        self.checkIgnoreErrors(targetHost)
        self.startedTime += (time.time() - before)
        self.results = []
        self.allResults[targetHost] = self.results
        self.skipTarget = None
        if not self.globalScanner:
            self.scanner = self.getDefaultScanner()
            if (self.requester.isDataFuzzing() and
                not self.matcher.comparatorIsSet()):
                co.infoBox("DataFuzzing detected, checking for a data comparator ...")
                before = time.time()
                self.scanner.updateMatcher(Matcher(
                    self.matcher.getAllowedStatus(),
                    self.getDataComparator()
                ))
                self.startedTime += (time.time() - before)

    def prepareFuzzer(self):
        """Prepare the fuzzer for the fuzzing tests.
           Refill the dictionary with the wordlist content if a global dictionary was given
        """
        if not self.globalDictionary:
            self.dictionary = self.dictionaries.get()
            self.totalRequests = len(self.dictionary)
        else:
            self.dictionary.reload()
        self.fuzzer = Fuzzer(
            requester=self.requester,
            dictionary=self.dictionary,
            scanner=self.scanner,
            delay=self.delay,
            numberOfThreads=self.numberOfThreads,
            resultCallback=self._resultCallback,
            exceptionCallbacks=[self._invalidHostnameCallback, self._requestExceptionCallback],
        )
        self.fuzzer.start()
        while self.fuzzer.join():
            if self.skipTarget:
                raise SkipTargetException(self.skipTarget)

    def getDefaultScanner(self):
        """Check what's the scanners that will be used
        
        @returns BaseScanner: The scanner used in the fuzzing tests
        """
        if self.requester.isUrlDiscovery():
            if isinstance(self.requester, SubdomainRequest):
                from ...core.scanners.default.SubdomainScanner import SubdomainScanner
                scanner = SubdomainScanner()
            else:
                from ...core.scanners.default.PathScanner import PathScanner
                scanner = PathScanner()
        else:
            from ...core.scanners.default.DataScanner import DataScanner
            scanner = DataScanner()
        scanner.updateMatcher(self.matcher)
        co.setMessageCallback(scanner.cliCallback)
        if (self.requester.isUrlDiscovery() and
            self.matcher.allowedStatusIsDefault()):
            scanner.updateMatcher(Matcher(
                Matcher.buildAllowedStatus("200-399,401,403"),
                self.matcher.getComparator(),
            ))
        return scanner

    def checkIgnoreErrors(self, host: str):
        """Check if the user wants to ignore the errors during the tests.
           By default, URL fuzzing (path and subdomain) ignore errors
        
        @type host: str
        @param host: The target hostname
        """
        if self.requester.isUrlFuzzing():
            self.ignoreErrors = True
            logPath = fh.logger.setup(host)
            co.infoBox(f'The logs will be saved on \'{logPath}\'')
        else:
            if co.askYesNo('info', "Do you want to ignore errors on this target, and save them into a log file?"):
                self.ignoreErrors = True
                logPath = fh.logger.setup(host)
                co.infoBox(f'The logs will be saved on \'{logPath}\'')
            else:
                self.ignoreErrors = False

    def getDataComparator(self):
        """Check if the user wants to insert custom data comparator to validate the responses
        
        @returns dict: The data comparator dictionary for the Matcher object
        """
        payload = ' ' # Set an arbitraty payload
        co.infoBox(f"Making first request with '{payload}' as payload ...")
        try:
            # Make the first request to get some info about the target
            response, RTT, *_ = self.requester.request(payload)
        except RequestException as e:
            raise SkipTargetException(f"{str(e)}")
        firstResult = self.scanner.getResult(
            response, self.requester.index,
            payload, RTT,
        )
        co.printResult(firstResult, False)
        length = None
        defaultLength = int(firstResult.length)+300
        if co.askYesNo('info', "Do you want to exclude responses based on custom length?"):
            length = co.askData(f"Insert the length (default {defaultLength})")
            if not length:
                length = defaultLength
            try:
                length = int(length)
            except ValueError:
                co.errorBox(f"The length ({length}) must be an integer")
        time = None
        defaultTime = firstResult.RTT+5.0
        if co.askYesNo('info', "Do you want to exclude responses based on custom time?"):
            time = co.askData(f"Insert the time (in seconds, default {defaultTime} seconds)")
            if not time:
                time = defaultTime
            try:
                time = float(time)
            except ValueError:
                co.errorBox(f"The time ({time}) must be a number")
        return Matcher.buildComparator(length, time)

    def showFooter(self):
        """Show the footer content of the software, after maked the fuzzing.
           The results are shown for each target
        """
        if self.fuzzer:
            if self.startedTime:
                co.infoBox(f"Time taken: {float('%.2f'%(time.time() - self.startedTime))} seconds")
            requesterIndex = 0
            for key, value in self.allResults.items():
                if value:
                    if self.isVerboseMode():
                        if not self.globalScanner:
                            self.requester = self.requesters[requesterIndex]
                            self.getDefaultScanner()
                        co.infoBox(f"Found {len(value)} matched results on target {key}:")
                        for result in value:
                            co.printResult(result, True)
                    reportPath = fh.reporter.open(key)
                    co.infoBox(f'Saving results for {key} on \'{reportPath}\' ...')
                    fh.reporter.write(value)
                    co.infoBox('Results saved')
                else:
                    co.infoBox(f"No matched results was found on target {key}")
                requesterIndex += 1

    def _skipCallback(self, status: int):
        """The skip target callback for the blacklistAction

        @type status: int
        @param status: The identified status code into the blacklist
        """
        self.skipTarget = f"Status code {str(status)} detected"
    
    def _waitCallback(self, status: int):
        """The wait (pause) callback for the blacklistAction

        @type status: int
        @param status: The identified status code into the blacklist
        """
        if not self.fuzzer.isPaused():
            if not self.isVerboseMode():
                co.print("")
            co.warningBox(f"Status code {str(status)} detected. Pausing threads ...")
            self.fuzzer.pause()
            if not self.isVerboseMode():
                co.print("")
            co.infoBox(f"Waiting for {self.blacklistStatus.actionParam} seconds ...")
            time.sleep(self.blacklistStatus.actionParam)
            co.infoBox("Resuming target ...")
            self.fuzzer.resume()

    def _resultCallback(self, result: dict, validate: bool):
        """Callback function for the results output

        @type result: dict
        @param result: The FuzzingTool result
        @type validate: bool
        @param validate: A validator flag for the result, gived by the scanner
        """
        if self.blacklistStatus and result.status in self.blacklistStatus.codes:
            self.blacklistStatus.actionCallback(result.status)
        else:
            if self.verbose[0]:
                if validate:
                    self.results.append(result)
                co.printResult(result, validate)
            else:
                if validate:
                    self.results.append(result)
                    co.printResult(result, validate)
                co.progressStatus(
                    result.index, self.totalRequests
                )
    
    def _requestExceptionCallback(self,
        e: RequestException,
        payload: str
    ):
        """Callback that handle with the request exceptions
        
        @type e: RequestException
        @param e: The request exception
        @type payload: str
        @param payload: The payload used in the request
        """
        if self.ignoreErrors:
            if not self.verbose[0]:
                co.progressStatus(
                    self.requester.index, self.totalRequests
                )
            else:
                if self.verbose[1]:
                    co.notWorkedBox(str(e))
            with self.lock:
                fh.logger.write(str(e), payload)
        else:
            self.skipTarget = str(e)

    def _invalidHostnameCallback(self, e: InvalidHostname):
        """Callback that handle with the subdomain hostname resolver exceptions
        
        @type e: InvalidHostname
        @param e: The invalid hostname exception
        """
        if self.verbose[0]:
            if self.verbose[1]:
                co.notWorkedBox(str(e))
        else:
            co.progressStatus(
                self.requester.index, self.totalRequests
            )

    def __initRequesters(self, parser: CliArgumentParser):
        """Initialize the requesters

        @type parser: CliArgumentParser
        @param parser: The command line interface arguments object
        """
        targets = []
        if parser.targetsFromUrl:
            targets.extend(AB.buildTargetsFromArgs(
                parser.targetsFromUrl, parser.method, parser.data
            ))
        if parser.targetsFromRawHttp:
            targets.extend(AB.buildTargetsFromRawHttp(
                parser.targetsFromRawHttp, parser.scheme
            ))
        if not targets:
            raise Exception("A target is needed to make the fuzzing")
        for target in targets:
            co.infoBox(f"Set target URL: {target['url']}")
            co.infoBox(f"Set request method: {target['methods']}")
            if target['data']:
                co.infoBox(f"Set request data: {target['data']}")
            if checkForSubdomainFuzz(target['url']):
                requestType = 'SubdomainRequest'
            else:
                requestType = 'Request'
            requester = HttpFactory.requestCreator(
                requestType,
                url=target['url'],
                methods=target['methods'],
                data=target['data'],
                headers=target['header'],
                followRedirects=parser.followRedirects,
                proxy=parser.proxy,
                proxies=fh.read(parser.proxies) if parser.proxies else [],
                timeout=parser.timeout,
                cookie=parser.cookie,
            )
            self.requesters.append(requester)

    def __initDictionary(self, parser: CliArgumentParser):
        """Initialize the dictionary

        @type parser: CliArgumentParser
        @param parser: The command line interface arguments object
        """
        def buildDictionary(name: str, params: str, requester: Request):
            """Build the dictionary

            @type name: str
            @param name: The dictionary name
            @type params: str
            @param params: The dictionary parameters
            @type requester: Request
            @param requester: The requester for the given dictionary
            @returns Dictionary: The dictionary object
            """
            co.infoBox(f"Building dictionary from {name} wordlist ...")
            try:
                dictionary = DictFactory.creator(name, params, requester)
            except Exception as e:
                raise Exception(str(e))
            co.infoBox(f"Dictionary is done, loaded {len(dictionary)} payloads")
            dictionary.setPrefix(parser.prefix)
            dictionary.setSuffix(parser.suffix)
            if parser.lowercase:
                dictionary.setLowercase()
            elif parser.uppercase:
                dictionary.setUppercase()
            elif parser.capitalize:
                dictionary.setCapitalize()
            if parser.encoder:
                dictionary.setEncoder(parser.encoder)
            return dictionary
        
        self.globalDictionary = None
        self.dictionaries = []
        if len(parser.wordlists) != len(self.requesters):
            name, params = parser.wordlists[0]
            self.globalDictionary = buildDictionary(name, params, None)
            self.dictionary = self.globalDictionary
            self.totalRequests = len(self.dictionary)
        else:
            self.dictionaries = Queue()
            for i, dictionary in enumerate(parser.wordlists):
                name, params = dictionary
                self.dictionaries.put(buildDictionary(name, params, self.requesters[i]))