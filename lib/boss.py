# Copyright (C) 2008 by Yusuke Horie <youthhr at gmail dot com>

from google.appengine.api import urlfetch
import urllib
import xml.dom.minidom


class BossBase:
    base_url = None

    def __init__(self, appid='uJQoL1LV34Et7aV1KkN.TFgFo90UldGSf1SbEmLiTGBBNIqIyqiA88D9jVgO2w--'):
        self.appid = appid

    def get_base_url(self):
        return self.base_url

    def get_request_url(self):
        return self.request_url

    def _send_request(self, url, options={}):
        if options: url = url + '?' + urllib.urlencode(options)

        self.request_url = url

        result = urlfetch.fetch(
            url = url,
            headers = {'Accept-encoding' : ''})

        if not result.status_code == 200:
            raise BossError, 'BOSS return status code: %s, url: %s' % (result.status_code, self.get_request_url())

        return Response(result.content)

class WebSearch(BossBase):
    base_url = "http://boss.yahooapis.com/ysearch/web/v1/%s"
    options = {
        'format'  : 'xml',
        'filter'  : '-porn',
        'count'   : '25',
    }

    def get(self, query, options={}):
        options['appid'] = self.appid
        url = self.base_url % urllib.quote_plus(query)
        self.options.update(options)
        res = self._send_request(url, self.options)
        return res.parse()


class Response:
    def __init__(self, content=None):
        self.content = content
        self._node = xml.dom.minidom.parseString(content)

    def get_content(self):
        return self.content

    def parse(self):
        items = []
        for n in self._node.getElementsByTagName('result'):
            items.append( {
                'title' : self._get_data('title', n),
                'url' : self._get_data('url', n),
                'dispurl' : self._get_data('dispurl', n),
                'abstract' : self._get_data('abstract', n),
                'size' : self._get_data('size', n),
            })
        return items

    def _get_node (self, nodename, node = None):
        if node is None : node = self._node
        elm = node.getElementsByTagName(nodename)
        return elm[0] if elm else None

    def _get_datas (self, nodename, node = None):
        if node is None : node = self._node
        categories = []
        for elm in node.getElementsByTagName(nodename):
            categories.append(elm.firstChild.data)
        return categories

    def _get_data (self, nodename, node = None):
        if node is None : node = self._node
        elm = node.getElementsByTagName(nodename)
        #return elm[0].firstChild.data.rstrip().lstrip() if elm else ''
        data = ''
        if elm and elm[0].firstChild:
            data = elm[0].firstChild.data.rstrip().lstrip()
        return data

    def _get_attribute (self, nodename, attrname, node = None):
        if node is None : node = self._node
        return node.getElementsByTagName(nodename)[0].getAttribute(attrname).rstrip().lstrip()

class BossError(Exception):
    """Used to indicate that an error occurred when trying to access AAWS via its API."""

    
