#!/usr/bin/python
# -*- coding: UTF-8 -*
import oauth
import urllib
import urllib2
import urlparse


Consumer = {
    '0': {'key': 'your consumer key', 'secret': 'your consumer secret'},     #上邪
    '1': {'key': 'your consumer key', 'secret': 'your consumer secret'},     #Mr.Greeting
    '2': {'key': 'your consumer key', 'secret': 'your consumer secret'},     #Mrs.Greeting
    '3': {'key': 'your consumer key', 'secret': 'your consumer secret'},     #小叔子的侄媳妇
}

class Client():
    def __init__( self, consumer, oauth_token={}):
        self.__consumer = oauth.OAuthConsumer(consumer['key'], consumer['secret'])
        self.__token = oauth.OAuthToken(oauth_token['key'], oauth_token['secret']) if oauth_token else None
        self.signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.base_url = 'http://api.fanfou.com%s.json'
        self.authorize_url = 'http://m.fanfou.com/oauth/authorize'
        self.access_token_url = 'http://fanfou.com/oauth/access_token'
        self.request_token_url = 'http://fanfou.com/oauth/request_token'

    def request(self, uri, method='GET', body={}, headers=None):
        if uri.startswith('/'):
            if ':' in uri:
                uri, arg = uri.split(':')
                uri = uri + body[arg]
            uri = self.base_url % uri
        if not isinstance(headers, dict): headers = {}
        if method == 'POST':
            headers['Content-Type'] = headers.get('Content-Type',  'application/x-www-form-urlencoded')
            parameters = body if headers.get('Content-Type') == 'application/x-www-form-urlencoded' else {}
        else:
            parameters = body
            uri = uri + '?' + urllib.urlencode(body) if body else uri
        req = oauth.OAuthRequest.from_consumer_and_token(self.__consumer,token=self.__token,http_url=uri,http_method=method,parameters=parameters)
        req.sign_request(self.signature_method, self.__consumer, self.__token)
        headers.update(req.to_header())
        req = urllib2.Request(uri, headers=headers)
        if headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            req.add_data(data=urllib.urlencode(body))
        elif method == 'POST':
            req.add_data(data=body)
        return urllib2.urlopen(req)

    def authorize(self):
        resp = self.request(self.request_token_url, 'GET')        
        request_token = dict(urlparse.parse_qsl(resp.read()))
        request_token['key'] = request_token.pop('oauth_token')
        request_token['secret'] = request_token.pop('oauth_token_secret')
        result = {
            'url': '%s?oauth_token=%s' % (self.authorize_url, request_token['key']),
            'request_token': request_token,
        }
        return result
        
    def access_token(self, request_token):
        self.__token = oauth.OAuthToken(request_token['key'], request_token['secret'])
        self.__token.set_verifier(request_token['key'])
        resp = self.request(self.access_token_url, 'POST')
        access_token = dict(urlparse.parse_qsl(resp.read()))
        access_token['key'] = access_token.pop('oauth_token')
        access_token['secret'] = access_token.pop('oauth_token_secret')
        return access_token

    def xauth(self, username, passwd):
        body = { 
            "x_auth_username": username,
            "x_auth_password": passwd,
            "x_auth_mode": 'client_auth'
        }
        resp = self.request(self.access_token_url, 'GET', body)
        access_token = dict(urlparse.parse_qsl(resp.read()))
        access_token['key'] = access_token.pop('oauth_token')
        access_token['secret'] = access_token.pop('oauth_token_secret')
        return access_token