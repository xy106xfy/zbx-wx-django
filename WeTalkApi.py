#!/usr/bin/env python
# coding=utf-8

import requests
import json
import os, time

## WeTalkApi class begin -----------------------------------------------------------------------------------------------
class WeTalkApi(object):
    def __init__(self, talk_type=0, token_time=7200, msg_max_size=3000, corp_id='', corp_secret='', agent_id=''):
        self.__corp_id = corp_id
        self.__corp_secret = corp_secret
        self.__agent_id = agent_id
        self.__msgtype = ['text', 'file', 'image', 'voice', 'video']
        self.__url_list = ['https://qyapi.weixin.qq.com/cgi-bin', 'https://oapi.dingtalk.com']
        if talk_type >= len(self.__url_list):
            talk_type = 0
        self.__get_token_url = self.__url_list[talk_type] + '/gettoken?corpid=%s&corpsecret=%s' % (corp_id, corp_secret)
        self.__up_file_url = self.__url_list[talk_type] + '/media/upload?type=file&access_token='
        self.__send_url = self.__url_list[talk_type] + '/message/send?access_token='
        self.__menu_url = self.__url_list[talk_type] + '/menu/'
        self.__msg_max_size = msg_max_size
        self.__token_time = token_time
        self.__token_last_time = 0
        self.__access_token = ''
    
    def get_access_token(self):
        now_time = int(time.time())
        if (not self.__access_token) or (now_time > self.__token_last_time):
            try:
                r = requests.get(self.__get_token_url)
                self.__access_token = r.json()['access_token']
                self.__token_last_time = now_time - 60 + self.__token_time
            except Exception as e:
                self.__access_token = ''
        return self.__access_token

    def get_media_ID(self, filename='test.txt'):
        access_token = self.get_access_token()
        if (not os.path.exists(filename)) or (not access_token):
            return ''
        up_file_url = self.__up_file_url + self.__access_token
        data = {'media': (os.path.basename(filename),  open(filename, 'rb'), 'application/octet-stream')}
        try:
            return requests.post(url=up_file_url, files=data).json()['media_id']
        except Exception as e:
            return ''
    
    def send_message(self, touser='', toparty='', totag='', msgtype='text', msg='hello', filename='test.txt', v_title='Title', v_description='Description'):
        date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        access_token = self.get_access_token()
        if not access_token:
            print u'[ %s ] : 获取 access_token 失败，无法发送消息！' % date_time
            return
        send_message_url = self.__send_url + access_token
        message_params = {
            "touser": '@all',
            "agentid": self.__agent_id,
            "safe": 0
        }
        if touser:
            if isinstance(touser, list):
                message_params['touser'] = '|'.join(touser)
            else:
                message_params['touser'] = touser
        if toparty:
            message_params['toparty'] = toparty
        if totag:
            message_params['totag'] = totag
        if msgtype not in self.__msgtype:
            msgtype = 'text'
        message_params['msgtype'] = msgtype
        message_params[msgtype] = {}
        if msgtype == 'text':
            if not msg:
                print u'[ %s ] : %s 发送不成功！无内容。' % (date_time, message_params['msgtype'])
                return ''
            if len(msg) > self.__msg_max_size:
                msg = msg[0:self.__msg_max_size]
            message_params[msgtype]['content'] = msg
        else:
            if (not os.path.exists(filename)):
                print u'[ %s ] : %s 发送不成功！文件不存在。' % (date_time, message_params['msgtype'])
                return ''
            message_params[msgtype]['media_id'] = self.get_media_ID(filename=filename)
            if not message_params[msgtype]['media_id']:
                print u'[ %s ] : 获取 %s media_id 失败，无法发送消息！' % (date_time, message_params['msgtype'])
                return
            if msgtype == 'video':
                message_params[msgtype]['title'] = v_title
                message_params[msgtype]['description'] = v_description
        # 开始发送消息
        try:
            r = requests.post(url=send_message_url, data=json.dumps(message_params))
            if r.json()['errmsg'] != 'ok':
                raise
            print '[ %s ] : %s message send ok!' % (date_time, message_params['msgtype'])
        except Exception as e:
            print '[ %s ] : %s message send error!' % (date_time, message_params['msgtype'])

    def send_menu(self, method='create', menu={}):
        date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        access_token = self.get_access_token()
        if not access_token:
            print u'[ %s ] : 获取 access_token 失败，无法 [ %s ] 目录！' % (date_time, method)
            return
        if (method != 'delete') and (method != 'create'):
            print u'[ %s ] : [ %s ] 不是一个有效的 method！' % (date_time, method)
            return
        if (method == u'create') and (not menu):
            print u'[ %s ] : [ %s ] 的 menu 不能为空！' % (date_time, method)
            return
        menu_url =  self.__menu_url + '%s?access_token=%s&agentid=%s' % (method, access_token, self.__agent_id)
        try:
            if method == "delete":
                r = requests.get(url=menu_url)
            elif method == "create":
                r = requests.post(url=menu_url, data=json.dumps(menu))
            if r.json()['errmsg'] != 'ok':
                raise
            print u'[ %s ] : [ %s ] menu ok!' % (date_time, method)
        except Exception as e:
            print e
            print u'[ %s ] : [ %s ] menu failed!' % (date_time, method)
## WeTalkApi class end -------------------------------------------------------------------------------------------------

'''
if __name__ == "__main__":
    corp_id = 'wwdf6ea09fe4017764'
    corp_secret = 'nBxOLPFS4Mgtu1agC--BSl1f1ca4y4VOGo61PWPkZuw'
    agent_id = '1000011'
    wapi = WeiXinAPI(corp_id=corp_id, corp_secret=corp_secret, agent_id=agent_id)
    #wapi.send_message(msg='haha, this is a test')
    #wapi.send_message(msgtype='file', filename='test.txt')
    #wapi.send_message(msgtype='image', filename='test.jpg')
    #wapi.send_message(msgtype='voice', filename='test.wav')
    access_token = wapi.get_access_token()
    #wapi.send_message(access_token=access_token, msg='haha, this is a test')
    #wapi.send_message(access_token=access_token, msgtype='file', filename='test.txt')
    #wapi.send_message(access_token=access_token, msgtype='image', filename='test.jpg')
    #wapi.send_message(access_token=access_token, msgtype='voice', filename='test.wav')
    wapi.send_message(access_token=access_token, msgtype='file', filename='WeiXinApi.py')
    wapi2 = WeiXinAPI(corp_id='wwdf6ea09fe4017764', corp_secret='yfX9PCwJ_75bYIFDYC9H2Up8XNRPANKQaoJUHllV5Kk', agent_id='1000012')
    wapi2.send_message(msg='test.xls')
'''
