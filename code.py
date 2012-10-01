#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import os
import web
import json
import time
import fanfou
import hashlib
import datetime
import mimetypes
import sae.const

urls = (
    '/friend.add/?([^/]*)/?', 'friend_add',
    '/friend.remove/?([^/]*)/?', 'friend_remove',
    '/friend.request/?', 'friend_request',
    '/friend.request/p\.(\d+)/?', 'friend_request',
    '/friend.acceptadd/([^/]*)/?', 'friend_acceptadd',
    '/friend.accept/([^/]*)/?', 'friend_accept',
    '/friend.deny/([^/]*)/?', 'friend_deny',
    '/friends/([^/]*)/?p\.(\d+)/?', 'friends',
    '/friends/?([^/]*)/?', 'friends',
    '/followers/([^/]*)/?p\.(\d+)/?', 'followers',
    '/followers/?([^/]*)/?', 'followers',
    '/mentions/?', 'mentions',
    '/mentions/p\.(\d*)', 'mentions',
    '/privatemsg/(\d+)/([^/]+)/(\d+)/?', 'privatemsg_viewreply',
    '/privatemsg/?', 'privatemsg',
    '/privatemsg/p\.(\d+)', 'privatemsg',
    '/privatemsg/sent/?', 'privatemsg_sent',
    '/privatemsg/sent/p\.(\d+)', 'privatemsg_sent',
    '/privatemsg.reply/?([^/]*)/?', 'privatemsg_reply',
    '/privatemsg.create/?([^/]*)/?', 'privatemsg_create',
    '/privatemsg.del/?([^/]*)/?', 'privatemsg_del',
    '/msg.new/?([^/]*)/?', 'msg_new',
    '/msg.del/?([^/]*)/?', 'msg_del',
    '/msg.reply/?([^/]*)/?', 'msg_reply',
    '/msg.forward/?([^/]*)/?', 'msg_forward',
    '/favorites/?([^/]*)/?', 'favorites',
    '/favorites/?([^/]*)/p\.(\d+)/?', 'favorites',
    '/msg.favorite.add/?([^/]*)/?', 'msg_favorite_add',
    '/msg.favorite.del/?([^/]*)/?', 'msg_favorite_del',
    '/userview/([^/]*)/?', 'userview',
    '/userview/([^/]*)/p\.(\d+)/?', 'userview',
    '/dialogue/([^/]*)/?', 'dialogue',
    '/dialogue/([^/]*)/p\.(\d+)/?', 'dialogue',
    '/statuses/([^/]*)/?([^/]*)/?', 'statuses',
    '/browse/?', 'browse',
    '/photo.del/?([^/]*)/?', 'photo_del',
    '/photo.upload/?', 'photo_upload',
    '/photo/([^/]*)/?([^/]*)/?', 'photo',
    '/photo.normal/([^/]*)/?([^/]*)/?', 'photo_normal',
    '/album/([^/]*)/p\.(\d+)/?', 'album',
    '/album/?([^/]*)/?', 'album',
    '/favorites/?', 'favorites',
    '/search/?', 'search',
    '/logout/?.*', 'logout',
    '/settings/?', 'settings',
    '/callback/?', 'callback',
    '/authorize/?', 'authorize',
    '/autologin.confirm/?', 'autologin_confirm',
    '/autologin/?', 'autologin',
    '/test/?', 'test',
    '/q/(.*)', 'query',
    '/', 'home',
    '/home/?', 'home',
    '/home/p\.(\d+)/?', 'home',
    '/([^/]+)/?', 'space',
    '/([^/]+)/p\.(\d+)/?', 'space',
)

class utils:
    @staticmethod
    def format_time(s):
        created_at = datetime.datetime.strptime(s, '%a %b %d %H:%M:%S +0000 %Y')
        minus = datetime.datetime.utcnow() - created_at
        if minus.days < 1:
            if minus.seconds < 60:
                s = '%s 秒前' % minus.seconds
            elif 60 <= minus.seconds < 3600:
                s = '%s 分钟前' % int(round(minus.seconds/60.0))
            else:
                s = '约 %s 小时前' % int(round(minus.seconds/3600.0))
        else:
            s = (created_at + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
        return s

    @staticmethod
    def format_birthday(s):
        year, month, day = s.encode('utf-8').split('-')
        s = ''
        if int(year): s += '%s 年' % year
        if int(month): s += ' %s 月' % int(month)
        if int(day): s += ' %s 日' % day
        return s

    @staticmethod
    def html_encode(s):
        el = {'&lt;': '<', '&gt;': '>', '&quot;': '"', '&amp;': '&'}
        for k in el.keys():
            s = s.replace(k, el[k])
        return s

    @staticmethod
    def replace_kw(s):
        return re.sub('<b>([^<]*)</b>', lambda m: '<strong>%s</strong>'%m.group(0), s).replace('http://fanfou.com', '')
    
    @staticmethod
    def b64str(s=None, key='web.py'):
        if not s: s = str(time.time())
        chars = [ 'a', 'b', 'c', 'd', 'e', 'f', 'g',
            'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 
            'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 
            'x', 'y', 'z', '0', '1', '2', '3', '4', 
            '5', '6', '7', '8', '9', 'A', 'B', 'C', 
            'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 
            'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
            'T', 'U', 'V', 'W', 'X', 'Y', 'Z',]
        result = []
        hexstr = hashlib.md5(s+key).hexdigest()
        for i in range(4):
            hexint = 0x3FFFFFFF & int('0x'+ hexstr[i*8: i*8+8], 16)
            outchars = ''
            for i in range(6):
                chr_i = 0x0000003D & hexint
                outchars += chars[chr_i]
                hexint = hexint >> 5
            result.append(outchars)
        return result[0]

    @staticmethod
    def rate_limit(func):
        def api_call(*args):
            try:
                return func(*args)
            except Exception:
                return utils.request('/account/rate_limit_status').read()
        return api_call

    @staticmethod
    def msg_raw_id(item):
        return item['repost_status_id'] if item.get('repost_status_id') else item['id']
        
    @staticmethod
    def pack_image(filename, image, status=None, file_type=None):
        # build the mulitpart-formdata body
        BOUNDARY = '---fanfaouEbq6fy'
        body = []
        if status is not None:
            body.append('--' + BOUNDARY)
            body.append('Content-Disposition: form-data; name="status"')
            body.append('Content-Type: text/plain; charset=US-ASCII')
            body.append('Content-Transfer-Encoding: 8bit')
            body.append('')
            body.append(status)
        body.append('--' + BOUNDARY)
        body.append('Content-Disposition: form-data; name="photo"; filename="%s"' % filename)
        body.append('Content-Type: %s' % file_type)
        body.append('Content-Transfer-Encoding: binary')
        body.append('')
        body.append(image)
        body.append('--' + BOUNDARY + '--')
        body.append('')
        body = '\r\n'.join(body)
        # build headers
        headers = {
            'Content-Type': 'multipart/form-data; boundary=' + BOUNDARY,
            'Content-Length': len(body)
        }
        return headers, body

    @staticmethod
    def authorize():
        if web.ctx.env.get('PATH_INFO') in ('/callback', '/authorize', '/autologin', '/test'): return
        env = web.cookies().get('consumer_env', '-1')
        if utils.oauth_token(env): return
        raise web.seeother('/authorize')

    @staticmethod
    def oauth_token(env='all'):
        oauth_token = web.cookies().get('oauth_token', '{}')
        if env == 'all':
            return eval(oauth_token)
        else:
            return eval(oauth_token).get(env)

    @staticmethod
    def client():
        env = web.cookies().get('consumer_env')
        oauth_token =  utils.oauth_token(env)
        client = fanfou.Client(fanfou.Consumer[env], oauth_token)
        return client

    @staticmethod
    def request(uri, method='GET', body={}, headers=None):
        client = utils.client()
        return client.request(uri, method, body, headers)

    @staticmethod
    def home_tl(body={}):
        resp = utils.request('/statuses/home_timeline', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def mentions(body={}):
        resp = utils.request('/statuses/mentions', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def mentions_show(body={}):
        msg_id = body.pop('id')
        start = body['page']
        for page in range(start, start+5):
            body['page'] = page
            data = utils.mentions(body)
            exist = map(lambda s: 1 if msg_id == s['id'] else 0, data)
            if sum(exist): break
        return data[exist.index(1)] if 1 in exist else {}

    @staticmethod
    def privatemsg(body={}):
        resp = utils.request('/direct_messages/inbox', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def privatemsg_sent(body={}):
        resp = utils.request('/direct_messages/sent', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def privatemsg_show(body={}, box='inbox'):
        msg_id = body.pop('id')
        page = 0
        data = None
        while 1:
            page += 1
            body['page'] = page
            resp = utils.request('/direct_messages/%s'%box, 'GET', body)
            data = json.loads(resp.read())
            exist = map(lambda s: 1 if msg_id == s['id'] else 0, data)
            if sum(exist): break
            if page > 3: break
        return data[exist.index(1)] if 1 in exist else {}

    @staticmethod
    def privatemsg_new(body={}):
        utils.request('/direct_messages/new', 'POST', body)

    @staticmethod
    def privatemsg_del(body={}):
        utils.request('/direct_messages/destroy', 'POST', body)

    @staticmethod
    def privatemsg_con(body={}):
        resp = utils.request('/direct_messages/conversation', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def friend_add(body={}):
        try:
            resp = utils.request('/friendships/create', 'POST', body)
            return resp.code
        except:
            return 403

    @staticmethod
    def friend_remove(body={}):
        utils.request('/friendships/destroy', 'POST', body)

    @staticmethod
    def friend_request(body={}):
        resp = utils.request('/friendships/requests', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def friend_accept(body={}):
        utils.request('/friendships/accept', 'POST', body)

    @staticmethod
    def friend_deny(body={}):
        utils.request('/friendships/deny', 'POST', body)

    @staticmethod
    def friend_acceptadd(body={}):
        utils.request('/friendships/accept', 'POST', body)
        utils.request('/friendships/create', 'POST', body)

    @staticmethod
    def friends(body={}):
        resp = utils.request('/users/friends', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def followers(body={}):
        resp = utils.request('/users/followers', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def browse(body={}):
        resp = utils.request('/statuses/public_timeline', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def search_public(body={}):
        resp = utils.request('/search/public_timeline', 'GET', body)
        return json.loads(resp.read())
        
    @staticmethod
    def search_users(body={}):
        resp = utils.request('/search/users', 'GET', body)
        return json.loads(resp.read())
        
    @staticmethod
    def search_user_tl(body={}):
        resp = utils.request('/search/user_timeline', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def space(body={}):
        resp = utils.request('/statuses/user_timeline', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def update(body={}, headers={}):
        utils.request('/statuses/update', 'POST', body, headers)
        web.setcookie('action', '发送成功！')
        raise web.seeother('/home')

    @staticmethod
    def update_profile(body={}):
        utils.request('/account/update_profile', 'POST', body)

    @staticmethod
    def album(body={}):
        resp = utils.request('/photos/user_timeline', 'GET', body)
        data = json.loads(resp.read())
        return data

    @staticmethod
    def photo(body={}):
        index = body.pop('index')
        resp = utils.request('/photos/user_timeline', 'GET', body)
        data = json.loads(resp.read())
        return data[index]

    @staticmethod
    def photo_upload(body={}, headers={}):
        utils.request('/photos/upload', 'POST', body, headers)

    @staticmethod
    def photo_count(body={}):
        count = cache.get(body['id']).get('photos_count', 0)
        if count: return count
        body['count'] = 60
        for page in range(1,6):
            body['page'] = page
            resp = utils.request('/photos/user_timeline', 'GET', body)
            data = json.loads(resp.read())
            count += len(data)
            page += 1
            if not data: break
        else:
            count = 300.0
        cache.set(body['id'], {'photos_count': count})
        return count

    @staticmethod
    def user_show(body={}):
        resp = utils.request('/users/show/:id', 'GET', body)
        data = json.loads(resp.read())
        visible = data['protected'] and data['following'] if data['protected'] else True
        visible = visible  or body['id'] == utils.user()['id']
        data['photos_count'] = utils.photo_count(body) if visible else 0
        return visible, data

    @staticmethod
    def msg_show(body={}):
        try:
            resp = utils.request('/statuses/show', 'GET', body)
            return json.loads(resp.read())
        except:
            return {}

    @staticmethod
    def msg_del(body={}):
        utils.request('/statuses/destroy', 'POST', body)

    @staticmethod
    def msg_favorite_add(body={}):
        return utils.request('/favorites/create/:id', 'POST', body)

    @staticmethod
    def msg_favorite_del(body={}):
        utils.request('/favorites/destroy/:id', 'POST', body)

    @staticmethod
    def favorites(body={}):
        resp = utils.request('/favorites/:id', 'GET', body)
        return json.loads(resp.read())

    @staticmethod
    def notice():
        notice = {}
        notice['now'] = utils.now()
        notice['action'] = web.cookies().get('action')
        web.setcookie('action', '')
        notice['id'] = utils.user()['id']
        notice['lover'] = { 'home2': 'paranoia7', 'paranoia7': 'home2' }.get(notice['id'])
        resp = utils.request('/account/notification', 'GET', {'mode': 'lite'})
        notice.update(json.loads(resp.read()))
        notice['trends'] = utils.trends()
        return notice


    @staticmethod
    def trends():
        if not web.cookies().get('trends') or utils.timed():
            resp = utils.request('/trends/list', 'GET')
            trends = json.loads(resp.read())['trends']
            web.setcookie('trends', trends)
            return trends
        else:
            return eval(web.cookies().get('trends'))

    @staticmethod
    def user():
        if not web.cookies().get('user'):
            user = {}
            try:
                resp = utils.request('/users/show', 'GET', {'mode': 'lite'})
                data = json.loads(resp.read())
                user['id'] = data['id']
                user['name'] = data['name']
                web.setcookie('user', user)
            except:
                user['id'] = 'null'
                user['name'] = 'null'
            return user
        else:
            return eval(web.cookies().get('user'))

    @staticmethod
    def timed():
        now = datetime.datetime.now()
        if now.minute % 20 == 0: return True

    @staticmethod
    def now():
        now = datetime.datetime.now()
        return now.strftime('%y/%m/%d %H:%M')

    @staticmethod
    def notfound():
        referer = web.ctx.env.get('HTTP_REFERER', web.ctx.home)
        referer = referer.replace(web.ctx.home, '')
        return web.notfound(render.unrealized(utils.user(), 404, referer, ''))

    @staticmethod
    def internalerror():
        referer = web.ctx.env.get('HTTP_REFERER', web.ctx.home)
        resp = utils.request('/account/rate_limit_status')
        data = json.loads(resp.read())
        if data['remaining_hits'] == 0:
            referer = referer.replace(web.ctx.home, 'http://m.fanfou.com')
            reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['reset_time_in_seconds']))
            return web.internalerror(render.unrealized(utils.user(), 403, referer, reset_time))
        else:
            referer = referer.replace(web.ctx.home, '')
            return web.internalerror(render.unrealized(utils.user(), 500, referer, ''))

class cache:
    @staticmethod
    def set(key, data):
        tmp = cache.get()
        if tmp.get(key):
            tmp[key]['*exp*'] = time.time()
        else:
            tmp[key] = {'*exp*': time.time()}
        tmp[key].update(data)
        for k,v in tmp.items():
            if v['*exp*'] + 600 < time.time():
                tmp.pop(k)
        web.setcookie('cache', tmp, 600)

    @staticmethod
    def get(key='all'):
        data = eval(web.cookies().get('cache', '{}'))
        if key == 'all':
            return data
        else:
            return data.get(key, {})
        
class home:
    def GET(self, page=1):
        body = {'page': page, 'format': 'html', 'mode': 'lite', 'count': 15}
        return render.home(utils.user(), utils.home_tl(body), int(page), utils.notice())

    def POST(self):
        wi = web.input()
        if wi.get('content') == web.cookies().get('last'):
            web.setcookie('action', '请勿发重复信息！')
            raise web.seeother('/home')
        web.setcookie('last', wi.content)
        body = { 'status': wi.content.encode('utf-8') }
        utils.update(body)

class msg_reply:
    def GET(self, msg_id):
        body = {'id': msg_id, 'mode': 'lite'}
        status = utils.msg_show(body)
        if not status:
            body.update({'page': 1, 'count': 15})
            status = utils.mentions_show(body)
        return render.msg_reply(utils.user(), status)

    def POST(self, msg_id):
        wi = web.input()
        body = { 'status': wi.content.encode('utf-8'), 'in_reply_to_status_id': msg_id }
        utils.update(body)

class msg_forward:
    def GET(self, msg_id):
        body = {'id': msg_id, 'mode': 'lite'}
        status = utils.msg_show(body)
        if not status:
            body.update({'page': 1, 'count': 15})
            status = utils.mentions_show(body)
        return render.msg_forward(utils.user(), status)

    def POST(self, msg_id):
        wi = web.input() 
        body = { 'status': wi.content.encode('utf-8'), 'repost_status_id': msg_id }
        utils.update(body)

class msg_new:
    def GET(self, user_id):
        body = {'id': user_id.encode('utf-8')}
        return render.msg_new(utils.user(), utils.user_show(body)[1])

    def POST(self, user_id):
        wi = web.input()
        body = { 
            'status': wi.content.encode('utf-8'),
            'in_reply_to_user_id': user_id.encode('utf-8')
        }
        utils.update(body)

class msg_del:
    def GET(self, msg_id):
        referer = web.ctx.env.get('HTTP_REFERER', '/home')
        referer = referer.replace(web.ctx.home, '')
        return render.msg_del(utils.user(), msg_id, referer)

    def POST(self, msg_id):
        body = {'id': msg_id }
        utils.msg_del(body)
        web.setcookie('action', '信息删除成功！')
        raise web.seeother(web.input().referer)

class msg_favorite_add:
    def GET(self, msg_id):
        body = {'id': msg_id}
        try:
            utils.msg_favorite_add(body)
        except:
            web.setcookie('action', '收藏失败，此消息不公开。')
        referer = web.ctx.env.get('HTTP_REFERER', '/home')
        raise web.seeother(referer)

class msg_favorite_del:
    def GET(self, msg_id):
        body = {'id': msg_id}
        utils.msg_favorite_del(body)
        referer = web.ctx.env.get('HTTP_REFERER', '/home')
        raise web.seeother(referer)

class favorites:
    def GET(self, user_id, page=1):
        body = {'id': user_id, 'count': 15, 'page': page, 'mode': 'lite', 'format': 'html'}
        visible, show = utils.user_show({'id': user_id})
        data = utils.favorites(body) if visible else []
        return render.favorites(utils.user(), visible, show, data, int(page), utils.notice())

class friend_request:
    def GET(self, page=1):
        body = {'count': 10, 'page': page}
        return render.friend_request(utils.user(), utils.friend_request(body), int(page), utils.notice())

class friend_acceptadd:
    def GET(self, user_id):
        body = {'id': user_id.encode('utf-8')}
        return render.friend_acceptadd(utils.user(), utils.user_show(body)[1])

    def POST(self, user_id):
        body = {'id': user_id.encode('utf-8')}
        utils.friend_acceptadd(body)
        if utils.notice()['friend_requests']:
            raise web.seeother('/friend.request')
        else:
            raise web.seeother('/home')

class friend_accept:
    def GET(self, user_id):
        body = {'id': user_id.encode('utf-8')}
        return render.friend_accept(utils.user(), utils.user_show(body)[1])

    def POST(self, user_id):
        body = {'id': user_id.encode('utf-8')}
        utils.friend_accept(body)
        if utils.notice()['friend_requests']:
            raise web.seeother('/friend.request')
        else:
            raise web.seeother('/home')

class friend_deny:
    def GET(self, user_id):
        body = {'id': user_id.encode('utf-8')}
        return render.friend_deny(utils.user(), utils.user_show(body)[1])

    def POST(self, user_id):
        body = {'id': user_id.encode('utf-8')}
        utils.friend_deny(body)
        if utils.notice()['friend_requests']:
            raise web.seeother('/friend.request')
        else:
            raise web.seeother('/home')

class friend_add:
    def GET(self, user_id):
        referer = web.ctx.env.get('HTTP_REFERER', '/home')
        referer = referer.replace(web.ctx.home, '')
        body = {'id': user_id.encode('utf-8'), 'mode': 'lite'}
        return render.friend_add(utils.user(), utils.user_show(body)[1], referer)

    def POST(self, user_id):
        wi = web.input()
        body = {'id': user_id.encode('utf-8')}
        if utils.friend_add(body) == 403:
            web.setcookie('action', '已向 %s 发出关注请求，请等待确认。' %wi.name.encode('utf-8'))
        else:
            web.setcookie('action', '你已成功关注 %s' %wi.name.encode('utf-8'))
        raise web.seeother(wi.referer)

class friend_remove:
    def GET(self, user_id):
        body = {'id': user_id.encode('utf-8'), 'mode': 'lite'}
        return render.friend_remove(utils.user(), utils.user_show(body)[1])

    def POST(self, user_id):
        wi = web.input()
        body = {'id': user_id.encode('utf-8'), 'mode': 'lite'}
        utils.friend_remove(body)
        web.setcookie('action', '已将 %s 从关注的人中删除。' %wi.name.encode('utf-8'))
        raise web.seeother(wi.referer)

class friends:
    def GET(self, user_id=None, page=1):
        if not user_id: user_id = utils.user()['id']
        body = {'id': user_id, 'mode': 'lite', 'count': 50, 'page': page}
        visible, show = utils.user_show({'id': user_id})
        data = utils.friends(body) if visible else []
        return render.friends(utils.user(), visible, show, data, int(page), utils.notice())

class followers:
    def GET(self, user_id=None, page=1):
        if not user_id: user_id = utils.user()['id']
        body = {'id': user_id, 'mode': 'lite', 'count': 50, 'page': page}
        visible, show = utils.user_show({'id': user_id})
        data = utils.followers(body) if visible else []
        return render.followers(utils.user(), visible, show, data, int(page), utils.notice())

class mentions:
    def GET(self, page=1):
        body = {'page': page, 'format': 'html', 'mode': 'lite', 'count': 15}
        return render.mentions(utils.user(), utils.mentions(body), int(page), utils.notice())

class privatemsg_viewreply:
    def GET(self, msg_id, box, page):
        body = {'id': msg_id, 'mode': 'lite', 'count': 60}
        raw_dm = utils.privatemsg_show(body, box)
        return render.privatemsg_viewreply(utils.user(), raw_dm, box, int(page), utils.notice())

class privatemsg:
    def GET(self, page=1):
        body = {'page': page, 'format': 'html', 'mode': 'lite', 'count': 10}
        return render.privatemsg(utils.user(), utils.privatemsg(body), int(page), utils.notice())

class privatemsg_sent:
    def GET(self, page=1):
        body = {'page': page, 'format': 'html', 'mode': 'lite', 'count': 10}
        return render.privatemsg_sent(utils.user(), utils.privatemsg_sent(body), int(page), utils.notice())

class privatemsg_reply:
    def GET(self, msg_id):
        body = {'id': msg_id, 'count':60, 'mode': 'lite'}
        raw_dm = utils.privatemsg_show(body)
        return render.privatemsg_reply(utils.user(), raw_dm)

    def POST(self, msg_id):
        wi = web.input()
        body = { 
            'user': wi.sendto.encode('utf-8'),
            'text': wi.content.encode('utf-8'),
            'in_reply_to_id': msg_id
        }
        utils.privatemsg_new(body)
        web.setcookie('action', '私信发送成功！')
        raise web.seeother('/home')

class privatemsg_create:
    def GET(self, user_id):
        referer = web.ctx.env.get('HTTP_REFERER', '/home')
        referer = referer.replace(web.ctx.home, '')
        return render.privatemsg_create(utils.user(), utils.user_show({'id':user_id})[1], referer, utils.notice())

    def POST(self, msg_id):
        wi = web.input()
        body = { 
            'user': wi.sendto.encode('utf-8'),
            'text': wi.content.encode('utf-8'),
        }
        utils.privatemsg_new(body)
        web.setcookie('action', '私信发送成功！')
        raise web.seeother(wi.referer)

class privatemsg_del:
    def GET(self, msg_id):
        referer = web.ctx.env.get('HTTP_REFERER', '/home')
        referer = '/privatemsg/sent' if 'sent' in referer else '/privatemsg'
        return render.privatemsg_del(utils.user(), msg_id, referer)

    def POST(self, msg_id):
        wi = web.input()
        body = {'id': msg_id }
        utils.privatemsg_del(body)
        web.setcookie('action', '私信删除成功！')
        raise web.seeother(wi.referer)

class statuses:
    def GET(self, msg_id, user_id):
        body = {'id': msg_id, 'mode': 'lite', 'format': 'html'}
        data = utils.msg_show(body)
        if data:
            return render.statuses(utils.user(), data, utils.notice())
        else:
            body = {'id': user_id.encode('utf-8'), 'mode': 'lite'}
            show = utils.user_show(body)
            if show[0]:
                return render.statuses_del(utils.user(),show[1], utils.notice())
            else:
                return render.statuses_lock(utils.user(),show[1], utils.notice())

class browse:
    def GET(self):
        body = { 'count': 15, 'format': 'html'}
        return render.browse(utils.user(), utils.browse(body), utils.notice())

class album:
    def GET(self, user_id, page=1):
        if not user_id: user_id = utils.user()['id']
        body = {'id': user_id, 'count': 10, 'mode': 'lite', 'page': page}
        visible, show = utils.user_show({'id': user_id})
        data = utils.album(body) if visible else []
        return render.album(utils.user(), visible, show, data, int(page), utils.notice())

class photo:
    def GET(self, mark, idx=0):   
        body = {'id': mark.encode('utf-8'), 'mode': 'lite', 'format': 'html'}
        if idx:
            index = int(idx)%20
            page = int(idx)/20
            page = page+1 if index else page
            body.update({'page': page, 'index': index-1})
            data = utils.photo(body)
            body.pop('page')
        else:
            data = utils.msg_show(body)
            body.update({'id': data['user']['id'].encode('utf-8'), 'count': 60})
            idx = [item['id'] for item in utils.album(body)].index(mark) + 1
            body.pop('count')
        return render.photo(utils.user(), utils.user_show(body)[1], data, int(idx), utils.notice())

class photo_normal:
    def GET(self, mark, idx=0):   
        body = {'id': mark.encode('utf-8'), 'mode': 'lite', 'format': 'html'}
        if idx:
            index = int(idx)%20
            page = int(idx)/20
            page = page+1 if index else page
            body.update({'page': page, 'index': index-1})
            data = utils.photo(body)
            body.pop('page')
        else:
            data = utils.msg_show(body)
            body.update({'id': data['user']['id'].encode('utf-8'), 'count': 60})
            idx = [item['id'] for item in utils.album(body)].index(mark) + 1
            body.pop('count')
        return render.photo_normal(utils.user(), utils.user_show(body)[1], data, int(idx), utils.notice())

class photo_upload:
    def GET(self):
        return render.photo_upload(utils.user(), utils.notice())

    def POST(self):
        wi = web.input(picture={})
        if wi.get('desc') == web.cookies().get('last'):
            web.setcookie('action', '请勿发重复信息！')
            raise web.seeother('/photo.upload')
        if not wi.picture.filename:
            web.setcookie('action', '请选择文件！')
            raise web.seeother('/photo.upload')
        file_type = mimetypes.guess_type(wi.picture.filename)[0]
        if file_type not in ['image/gif', 'image/jpeg', 'image/png', 'image/x-png']:
            return file_type
            web.setcookie('action', '照片格式错误')
            raise web.seeother('/photo.upload')
        headers, body = utils.pack_image(wi.picture.filename, wi.picture.file.read(), wi['desc'].encode('utf-8'), file_type)
        utils.photo_upload(body, headers)
        web.setcookie('last', wi.desc)
        web.setcookie('action', '发送成功！')
        raise web.seeother('/home')

class photo_del:
    def GET(self, msg_id):
        return render.photo_del(utils.user(), msg_id)

    def POST(self, msg_id):
        wi = web.input()
        body = {'id': msg_id }
        utils.msg_del(body)
        web.setcookie('action', '照片删除成功！')
        raise web.seeother('/album')
    
class search:
    def GET(self):
        wi = web.input()
        if wi.get('st') == '0':
            m = 'since_id' if wi.get('t') == '0' else 'max_id'
            body = {
                'q': wi.q.encode('utf-8'), 'format': 'html', 
                'count': 10, 'mode': 'lite', m: wi.get('m', '')
            }
            return render.search(utils.user(), wi, utils.search_public(body), utils.notice())
        elif wi.get('st') == '1':
            m = 'since_id' if wi.get('t') == '0' else 'max_id'
            body = {
                'q': wi.q.encode('utf-8'), 'format': 'html', 
                'count': 10, 'mode': 'lite', m: wi.get('m', '')
            }
            return render.search(utils.user(), wi, utils.search_user_tl(body), utils.notice())
        elif wi.get('st') == '2':
            p = int(wi.p) if wi.get('p') else 1
            body = {
                'q': wi.q.encode('utf-8'),  'format': 'html',
                'count': 10, 'mode': 'lite', 'page': p
            }
            return render.find(utils.user(), wi, utils.search_users(body), utils.notice())
        else:
            return render.search(utils.user(), wi, (), utils.notice())

class logout:
    def GET(self):
        web.setcookie('user', '')
        web.setcookie('oauth_token', '{}')
        web.setcookie('request_token', '')
        return render.authorize(200)

class query:
    def GET(self, word):
        body = {'q': word.encode('utf-8'), 'format': 'html', 'count': 10, 'mode': 'lite'}
        return render.q(utils.user(), word, utils.search_public(body), utils.notice())

class space:
    def GET(self, user_id, page=1):
        visible, show = utils.user_show({'id': user_id.encode('utf-8') })
        if visible:
            body = {'id': user_id.encode('utf-8'), 'page': page, 'format': 'html', 'mode': 'lite', 'count': 15}
            return render.space(utils.user(), show, utils.space(body), int(page), utils.notice())
        else:
            return render.space_lock(utils.user(), show, utils.notice())

class userview:
    def GET(self, user_id, page=1):
        visible, show = utils.user_show({'id': user_id.encode('utf-8') })
        if visible:
            body = {'id': user_id.encode('utf-8'), 'page': page, 'format': 'html', 'mode': 'lite', 'count': 15}
            return render.userview(utils.user(), show, utils.home_tl(body), int(page), utils.notice())
        else:
            return render.space_lock(utils.user(), show, utils.notice())

class dialogue:
    def GET(self, user_id, page=1):
        visible, show = utils.user_show({'id': user_id.encode('utf-8') })
        if visible:
            body = {'id': user_id.encode('utf-8'), 'page': page, 'format': 'html', 'mode': 'lite', 'count': 15}
            return render.dialogue(utils.user(), show, utils.privatemsg_con(body), int(page), utils.notice())
        else:
            return render.space_lock(utils.user(), show, utils.notice())

class settings:
    def GET(self):
        env = web.cookies().get('consumer_env')
        body = {'id': utils.user()['id'].encode('utf-8')}
        bio = utils.user_show(body)[1]['description']
        return render.settings(utils.user(), bio, env, 0)
    
    def POST(self):
        wi = web.input()
        body = {'name': wi.name.encode('utf-8'), 'description': wi.bio.encode('utf-8')}
        utils.update_profile(body)
        env = wi.consumer
        mod = 1 if utils.oauth_token(env) else 2
        user = utils.user()
        user.update({'name':wi.name})
        web.setcookie('user', user)
        web.setcookie('consumer_env', env)
        return render.settings(utils.user(), wi.bio, env, mod)



class callback:
    def GET(self):
        env = web.cookies().get('consumer_env')
        request_token = eval(web.cookies().get('request_token', '{}'))
        if request_token:
            client = fanfou.Client(fanfou.Consumer[env])
            oauth_token = utils.oauth_token()
            oauth_token.update({env: client.access_token(request_token)})
            web.setcookie('oauth_token', oauth_token)
            web.setcookie('request_token', '')
            raise web.seeother('/home')
        else:
            raise web.seeother('/authorize')

class authorize:
    def GET(self):
        env = web.cookies().get('consumer_env')
        if env:
            client = fanfou.Client(fanfou.Consumer[env])
            auth = client.authorize()
            web.setcookie('request_token', auth['request_token'])
            raise web.seeother(auth['url'])
        else:
            return render.authorize(200)

    def POST(self):
        env = web.input().consumer
        web.setcookie('consumer_env', env)
        if utils.oauth_token(env):
            raise web.seeother('/home')
        else:
            client = fanfou.Client(fanfou.Consumer[env])
            auth = client.authorize()
            web.setcookie('request_token', auth['request_token'])
            raise web.seeother(auth['url'])

class autologin_confirm:
    def GET(self):
        env = web.cookies().get('consumer_env')
        _token = utils.oauth_token(env)
        sid = utils.b64str(env) + utils.b64str(_token['key']) + utils.b64str(_token['secret'])
        database.token.set(sid, env, _token)
        raise web.seeother('/autologin?sid=%s'%sid)

class autologin:
    def GET(self):
        referer = web.ctx.env.get('HTTP_REFERER')
        http_host = web.ctx.env.get('HTTP_HOST')
        if referer and http_host in referer:
            return render.autologin()
        else:
            sid =  web.input().get('sid')
            _token = database.token.get(sid)
            if not _token: return render.authorize(404)
            _token.pop('sid')
            env = _token.pop('env')
            _token['key'] = _token.pop('token_key')
            _token['secret'] = _token.pop('token_secret')
            oauth_token = utils.oauth_token()
            oauth_token.update({env: _token})
            web.setcookie('consumer_env', env)
            web.setcookie('oauth_token', oauth_token)
            web.setcookie('user', '')
            raise web.seeother('/home')


class database:
    db = web.database(
        dbn = 'mysql',
        db = sae.const.MYSQL_DB,
        user = sae.const.MYSQL_USER,
        pw = sae.const.MYSQL_PASS,
        host = sae.const.MYSQL_HOST,
        port = int(sae.const.MYSQL_PORT),
    )

    class token:
        @staticmethod
        def set(sid, env, _token):
            if not database.token.get(sid):
                database.db.insert('token', sid=sid, env=env, token_key=_token['key'], token_secret=_token['secret'])

        @staticmethod
        def get(sid):
            res = list(database.db.select('token', where="sid='%s'"%sid))
            return dict(res[0]) if res else None



class test:
    def GET(self):
        #raise web.internalerror()
        return web.cookies()
    
path = os.path.dirname(os.path.abspath(__file__))
render = web.template.render(os.path.join(path, 'templates'), globals=globals())
web.config.debug = True
app = web.application(urls, globals()) 
#app.notfound = utils.notfound
#app.internalerror = utils.internalerror
app.add_processor(web.loadhook(utils.authorize))

if __name__ == '__main__':
    app.run()