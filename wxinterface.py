#!/usr/bin/env python
# -*- coding: utf-8 -*-
#########################################################################
import uuid, os, json
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from WXBizMsgCrypt import WXBizMsgCrypt
import xml.etree.cElementTree as ET
import sys
import thread
import ZabbixWeTalkApi
import time

# 企业微信上定义的 Token、加密密钥和企业微信ID，具体参见企业微信的开发文档
sToken = ""  
sEncodingAESKey = ""
sCorpID = ""

wxcpt=WXBizMsgCrypt(sToken,sEncodingAESKey,sCorpID)
zwapi = ''
wapi = ''

def wxinterface(request):
    global wxcpt
    global zwapi
    global wapi

    if request.method == 'GET':
        sVerifyMsgSig = request.GET.get('msg_signature')
        sVerifyTimeStamp =  request.GET.get('timestamp')
        sVerifyNonce = request.GET.get("nonce")
        sVerifyEchoStr = request.GET.get("echostr")
        ret,sEchoStr=wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp,sVerifyNonce,sVerifyEchoStr)
        if(ret!=0):
            print "ERR: VerifyURL ret: " + str(ret)
            sys.exit(1)
        return HttpResponse(sEchoStr)
    elif request.method == 'POST':
        sReqMsgSig = request.GET.get('msg_signature')
        sReqTimeStamp = request.GET.get('timestamp')
        sReqNonce = request.GET.get("nonce")
        sReqData = request.body
        ret,sMsg = wxcpt.DecryptMsg(sReqData, sReqMsgSig, sReqTimeStamp, sReqNonce)
        if( ret!=0 ):
            print "ERR: DecryptMsg ret: " + str(ret)
            sys.exit(1)
        xml_tree = ET.fromstring(sMsg)
        try:
            toUser = xml_tree.find('ToUserName').text
            fromUser = xml_tree.find('FromUserName').text
            agentid = xml_tree.find('AgentID').text
            msgType = xml_tree.find('MsgType').text
            if msgType == 'text':
                content = xml_tree.find('Content').text
            elif msgType == 'event':
                event = xml_tree.find('Event').text
                content = xml_tree.find('EventKey').text
        except Exception as e:
            print e
            sys.exit(1)
        time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(sReqTimeStamp)))
        logfile = open('wxinterface.log','a')
        # 根据content内容，取相对应的信息，主动发送到对应的人
        if content:
            log_content = time_str + u', 用户:' + fromUser + u', 发送至:' + agentid  +  u', 事件类型:' + msgType + u', 命令:' + content + u' ,命令长度:' + str(len(content))
            if not zwapi:
                zwapi = ZabbixWeTalkApi.ZabbixWeTalkApi(config_file='WeiXinByGroup.conf')
                #wapi = zwapi.w_dic['WX_iGet']['wapi']
            for wx in zwapi.w_dic.values():
                if agentid in wx.values():
                    touser_list = [fromUser, 'user1', 'user2', 'user3']
                    wapi = wx['wapi']
                    if wapi:
                        para = tuple([wapi, content.strip(), touser_list])
                        thread.start_new_thread(zwapi.AutoSendAlertInfo,para)
                        wapi.send_message(touser=['user1','user2'],msg=log_content)
                    else:
                        sys.exit(1)
        else:
            log_content = time_str + u', 用户:' + fromUser + u', 事件类型:' + msgType + u', 动作:' + event          
        logfile.write(log_content + '\n')
        logfile.close()
        return HttpResponse('ok')
