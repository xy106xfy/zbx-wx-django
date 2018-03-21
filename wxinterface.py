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

sToken = "hJqcu3uJ9Tn2gXPmxx2w9kkCkCE2EPYo"
sEncodingAESKey = "6qkdMrs68nhKduznJYO1A37W2oEgpkMUvkttRToqhUt"
sCorpID = "wwdf6ea09fe4015784"

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
        context = {}
        context['content'] = sEchoStr
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
            msgType = xml_tree.find('MsgType').text
            if msgType == 'text':
                content = xml_tree.find('Content').text
            elif msgType == 'event':
                content = xml_tree.find('EventKey').text
        except Exception as e:
            sys.exit(1)
        context = {}
        context['content'] = content
        time_str = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(sReqTimeStamp)))
        logfile = open('/opt/work/wxinterface.log','a')
        log_content = time_str + u', 用户:' + fromUser + u', 事件类型:' + msgType + u', 命令:' + content + u' ,命令长度:' + str(len(content))
        logfile.write(log_content + '\n')
        logfile.close()
        #WXEnterprise.AutoSendAlertInfo(cmd_msg=content) 
        if not zwapi or not wapi:
            zwapi = ZabbixWeTalkApi.ZabbixWeTalkApi(config_file='WeiXinByGroup.conf', wt_iGet=True)
            wapi = zwapi.w_dic['WX_iGet']['wapi']
        # 根据content内容，取相对应的信息，主动发送到对应的人
        touser = fromUser # + '|UserName1|UserName2' ,如果要增加其他人收到消息
        para_list = [wapi, content.strip(), touser]
        para = tuple(para_list)
        # 启用线程，调用主动发送接口
        thread.start_new_thread(zwapi.AutoSendAlertInfo,para)
        #zwapi.AutoSendAlertInfo(wapi=wapi, cmd_msg=content)
        return HttpResponse('ok')
