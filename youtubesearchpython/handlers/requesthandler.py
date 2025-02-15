from os import environ
from urllib.request import Request, urlopen, ProxyHandler, build_opener, install_opener
from urllib.parse import urlencode, urlparse
import json
import copy
from youtubesearchpython.handlers.componenthandler import ComponentHandler
from youtubesearchpython.internal.constants import *


class RequestHandler(ComponentHandler):
    def _makeRequest(self) -> None:
        ''' Fixes #47 '''
        requestBody = copy.deepcopy(requestPayload)
        requestBody['query'] = self.query
        requestBody['client'] = {
            'hl': self.language,
            'gl': self.region,
        }
        if self.searchPreferences:
            requestBody['params'] = self.searchPreferences
        if self.continuationKey:
            requestBody['continuation'] = self.continuationKey
        requestBodyBytes = json.dumps(requestBody).encode('utf_8')
        request = Request(
            'https://www.youtube.com/youtubei/v1/search' + '?' + urlencode({
                'key': searchKey,
            }),
            data = requestBodyBytes,
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Content-Length': len(requestBodyBytes),
                'User-Agent': userAgent,
            }
        )

        try:
            http_proxy = environ["HTTP_PROXY"]
        except KeyError:
            pass
        else:
            #request.set_proxy(urlparse(http_proxy).netloc, "http")
            proxy_support = ProxyHandler({'http': urlparse(http_proxy).netloc})
            opener = build_opener(proxy_support)
            install_opener(opener)

        try:
            self.response = urlopen(request, timeout=self.timeout).read().decode('utf_8')
        except:
            raise Exception('ERROR: Could not make request.')
    
    def _makeChannelSearchRequest(self) -> None:
        ''' Fixes #47 '''
        requestBody = copy.deepcopy(requestPayload)
        requestBody['query'] = self.query
        requestBody['client'] = {
            'hl': self.language,
            'gl': self.region,
        }
        requestBody['params'] = self.searchPreferences
        requestBody['browseId'] = self.browseId

        requestBodyBytes = json.dumps(requestBody).encode('utf_8')
        request = Request(
            'https://www.youtube.com/youtubei/v1/browse' + '?' + urlencode({
                'key': searchKey,
            }),
            data = requestBodyBytes,
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Content-Length': len(requestBodyBytes),
                'User-Agent': userAgent,
            }
        )
        try:
            self.response = json.loads(urlopen(request).read().decode('utf_8'))
        except:
            raise Exception('ERROR: Could not make request.')
    
    def _parseSource(self) -> None:
        try:
            if not self.continuationKey:
                responseContent = self._getValue(json.loads(self.response), contentPath)
            else:
                responseContent = self._getValue(json.loads(self.response), continuationContentPath)
            if responseContent:
                for element in responseContent:
                    if itemSectionKey in element.keys():
                        self.responseSource = self._getValue(element, [itemSectionKey, 'contents'])
                    if continuationItemKey in element.keys():
                        self.continuationKey = self._getValue(element, continuationKeyPath)
            else:
                self.responseSource = self._getValue(json.loads(self.response), fallbackContentPath)
                self.continuationKey = self._getValue(self.responseSource[-1], continuationKeyPath)
        except:
            raise Exception('ERROR: Could not parse YouTube response.')
    
    def _parseChannelSearchSource(self) -> None:
        try:
            self.response = self.response["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][-1]["expandableTabRenderer"]["content"]["sectionListRenderer"]["contents"]
        except:
            raise Exception('ERROR: Could not parse YouTube response.') 
