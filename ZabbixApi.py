#!/usr/bin/env python
# coding=utf-8

import json
import requests

## ZabbixApi class begin -----------------------------------------------------------------------------------------------
class ZabbixApi(object):
    def __init__(self, server='', username='', password=''):
        self.__url = server + '/api_jsonrpc.php'
        self.__headers = { 'Content-Type': 'application/json-rpc', 'User-Agent': 'python/zabbix_api'}
        self.__username = username
        self.__password = password
        self.__id = 0
        self.__auth = ''
        self.login()

    def json_obj(self, method='', params={}, auth=False):
        obj = {'jsonrpc': '2.0',
               'method': method,
               'params': params,
               'auth': self.__auth,
               'id': self.__id}
        if auth:
            del obj['auth']
        return json.dumps(obj)

    def postRequest(self, jsonObj=''):
        try:
            re = requests.post(self.__url, jsonObj, headers=self.__headers)
            response = json.loads(re.text)
            self.__id += 1
            return response['result']
        except Exception as e:
            print e
            return ''

    def login(self):
        if self.__auth == '':
            obj = self.json_obj(method='user.login', params={'user': self.__username, 'password': self.__password}, auth=True)
            self.__auth = self.postRequest(jsonObj=obj)
        return self.__auth != ''

    def isLogin(self):
        return self.__auth != ''

    def zbcall(self, method='', params={}):
        if not method:
            return ''
        return self.postRequest(jsonObj=self.json_obj(method=method, params=params))

    def str2list(self, sstr='', spl=','):
        if isinstance(sstr, str):
            return [ss.strip() for ss in sstr.split(spl) if ss.strip()]
        return sstr

    def host_get(self, output='', selectInterfaces='', templateids='', hostids='', para_ext={}):
        if not output:
            params = {'output': 'extend'}
        else:
            params = {'output': self.str2list(sstr=output)}
        if selectInterfaces:
            params['selectInterfaces'] = self.str2list(sstr=selectInterfaces)
        if hostids:
            params['hostids'] = hostids
        if templateids:
            params['templateids'] = templateids
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='host.get', params=params)

    def item_get(self, output='', templateids='', hostids='', ac=0, para_ext={}):
        if not output:
            params = {'output': 'extend'}
        else:
            params = {'output': self.str2list(sstr=output)}
        if templateids:
            params['templateids'] = templateids
        if hostids:
            params['hostids'] = hostids
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        if ac != 0:
            if 'filter' not in params.keys():
                params['filter'] = {}
            if ac == 3:
                params['filter']['state'] = 1
                params['filter']['status'] = 0
            elif ac == 2:
                params['filter']['status'] = 1
            elif ac == 1:
                params['filter']['state'] = 0
                params['filter']['status'] = 0
        return self.zbcall(method='item.get', params=params)

    def item_delete(self, itemid=[]):
        if itemid:
            return self.zbcall(method='item.delete', params=itemid)
        return ''

    def item_update(self, itemid='', para_ext={}):
        if not itemid:
            return ''
        params = {}
        params['itemid'] = itemid
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='item.update', params=params)

    def hostgroup_get(self, output='', hostids='', groupname='', para_ext={}):
        if not output:
            params = {'output': 'extend'}
        else:
            params = {'output': self.str2list(sstr=output)}
        if hostids:
            params['hostids'] = hostids
        if groupname:
            params['filter']['name'] = groupname
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='hostgroup.get', params=params)

    def hostgroup_id_list(self, name=''):
        group_id_list = []
        name = name.replace(' ', '')
        if name:
            name_list = name.split('|')
            group_list = self.hostgroup_get(output='name')
            group_id_list = [group['groupid'] for group in group_list for ss in name_list if ss in group['name'].lower()]
        return group_id_list

    def hostgroup_create(self, groupname=''):
        if groupname:
            group_info = self.hostgroup_get(output='groupid', groupname=groupname)
            if group_info:
                return group_info[0]['groupid']
            params = {'name': groupname}
            rstr = self.zbcall(method='hostgroup.create', params=params)
            if rstr:
                return rstr['groupids'][0]
        return '-1'

    def template_get(self, output='', templateids='', hostids='', para_ext={}):
        if not output:
            params = {'output': 'extend'}
        else:
            params = {'output': self.str2list(sstr=output)}
        if templateids:
            params['templateids'] = templateids
        if hostids:
            params['hostids'] = hostids
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='template.get', params=params)

    def template_massadd(self, templates='', host=''):
        template_list = self.template_get(output='templateid', para_ext={'filter': {'host': self.str2list(sstr=templates)}})
        host_list = self.host_get(output='hostid', para_ext={'filter': {'host': self.str2list(sstr=host)}})
        return self.zbcall(method='template.massadd', params={"templates": template_list, "hosts": host_list})

    def template_massremove(self, templates='', host='', itemdel=False):
        template_list = self.template_get(output='templateid', para_ext={'filter': {'host': self.str2list(sstr=templates)}})
        host_list = self.host_get(output='hostid', para_ext={'filter': {'host': self.str2list(sstr=host)}})
        template_id = []
        host_id = []
        for temp in template_list:
            template_id.append(temp['templateid'])
        for host in host_list:
            host_id.append(host['hostid'])
        return self.zbcall(method='template.massremove', params={'templateids': template_id, 'hostids': host_id})

    def history_get(self, itemids='', history=3, limit=10, sortfield='', sortorder='', para_ext={}):
        params = {'output': 'extend', 'history': 3, 'limit': limit}
        if itemids:
            params['itemids'] = itemids
        if history != 3:
            params['history'] = history
        if limit != 10:
            params['limit'] = limit
        if sortfield:
            params['sortfield'] = sortfield
        if sortorder:
            params['sortorder'] = sortorder
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='history.get', params=params)

    def isItemInHost(self, host='', hostid='', key_=''):
        if ((not host) and (not hostid)) or (not key_):
            return False
        if not hostid:
            hostid_list = self.host_get(output='hostid', para_ext={'filter': {'host': host}})
            if len(hostid_list) == 0:
                return False
            hostid = hostid_list[0]['hostid']
        return len(self.item_get(output='itemid', hostids=hostid, para_ext={'filter': {'key_': key_}})) > 0

    def isTempInHost(self, host='', hostid='', thost=''):
        if ((not host) and (not hostid)) or (not thost):
            return False
        if not hostid:
            hostid_list = self.host_get(output='hostid', para_ext={'filter': {'host': host}})
            if len(hostid_list) == 0:
                return False
            hostid = hostid_list[0]['hostid']
        return len(self.template_get(output='itemid', hostids=hostid, para_ext={'filter': {'host': thost}})) > 0

    def alert_get(self, output='', alertids='', actionids='', groupids='', selectHosts='', time_from='', time_till='', para_ext={}):
        if not output:
            params = {'output': 'extend'}
        else:
            params = {'output': self.str2list(sstr=output)}
        if alertids:
            params['alertids'] = alertids
        if actionids:
            params['actionids'] = actionids
        if groupids:
            params['groupids'] = groupids
        if selectHosts:
            params['selectHosts'] = self.str2list(sstr=selectHosts)
        if time_from:
            params['time_from'] = time_from
        if time_till:
            params['time_till'] = time_till
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='alert.get', params=params)

    def get_item_unsupported(self, prt=False):
        rdic = {}
        item_list = self.item_get(output='itemid, hostid, templateid, value_type, key_', ac=3)
        num = len(item_list)
        if num > 0:
            for item in item_list:
                hostid = item['hostid']
                if hostid not in rdic.keys():
                    rdic[hostid] = {}
                    rdic[hostid]['unsum'] = 1
                    rdic[hostid]['ip'] = ''
                    rdic[hostid]['port'] = ''
                    rdic[hostid]['name'] = ''
                    rdic[hostid]['host'] = ''
                    rdic[hostid]['uninfo'] = []
                    try:
                        tmp_dic = self.host_get(output='name, host', selectInterfaces='ip, port', hostids=hostid)[0]
                    except Exception, e:
                        print hostid, ': search is error!'
                    else:
                        rdic[hostid]['ip'] = tmp_dic['interfaces'][0]['ip']
                        rdic[hostid]['port'] = tmp_dic['interfaces'][0]['port']
                        rdic[hostid]['name'] = tmp_dic['name']
                        rdic[hostid]['host'] = tmp_dic['host']
                else:
                    rdic[hostid]['unsum'] += 1
                rdic[hostid]['uninfo'].append({'itemid': item['itemid'], 'value_type': item['value_type'], 'hostid': item['hostid'],
                                            'templateid': item['templateid'], 'key_': item['key_']})
        if prt:
            print '----------------------------------------------------------------------------------------'
            print 'total unsupported item key is: ', num
            print '----------------------------------------------------------------------------------------'
            m = 0
            for hostid in rdic.keys():
                m += 1
                tmp_dic = rdic[hostid]
                print '[', tmp_dic['unsum'], ']', m, '.\t', tmp_dic['ip'], '\t', tmp_dic['port'], '\t', tmp_dic['name'], '\t', tmp_dic['host']
                tmp_list = rdic[hostid]['uninfo']
                n = 0
                for item in tmp_list:
                    n += 1
                    print '\t(', n, ')', item['itemid'], '\t', item['value_type'], '\t', item['hostid'], '\t', item['templateid'], '\t', item['key_']
        rdic['unsum'] = num
        return rdic

    def sort_host_item(self, limit=10):
        rdic = {}
        temp_list = self.template_get(output='templateid, host, name')
        for item in temp_list:
            host_list = self.host_get(output='hostid, host, name', templateids=item['templateid'])
            print item['host']
            num = len(host_list)
            if num == 0:
                continue
            rdic[item['templateid']] = {}
            rdic[item['templateid']]['host'] = item['host']
            rdic[item['templateid']]['name'] = item['name']
            rdic[item['templateid']]['num'] = num
            rdic[item['templateid']]['content'] = host_list
        #rdic = {'1':{'num':18, 'name':'hehe1', 'host':'haha1', 'content':[2,3,4]}, '3':{'num':20, 'name':'hehe2', 'host':'haha2', 'content':[2,3,4]},'2':{'num':12, 'name':'hehe3', 'host':'haha3', 'content':[2,3,4]}}
        sort_d = sorted(rdic.items(), key=lambda d: d[1]["num"], reverse=True)[:limit:]
        print sort_d

    def problem_get(self, output='', selectTags='',eventids='', groupids='', hostids='', objectids='', para_ext={}):
        if not output:
            params = {'output': 'extend'}
        else:
            params = {'output': self.str2list(sstr=output)}
        if not selectTags:
            params['selectTags'] = 'extend'
        else:
            params['selectTags'] = self.str2list(sstr=selectTags)
        if eventids:
            params['eventids'] = eventids
        if groupids:
            params['groupids'] = groupids
        if hostids:
            params['hostids'] = hostids
        if objectids:
            params['objectids'] = objectids
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='problem.get', params=params)

    def trigger_get(self, output='', selectGroups='', selectHosts='', triggerids='', groupids='', templateids='', hostids='', itemids='', para_ext={}):
        if not output:
            params = {'output': 'extend'}
        else:
            params = {'output': self.str2list(sstr=output)}
        if selectGroups:
            params['selectGroups'] = self.str2list(sstr=selectGroups)
        if selectHosts:
            params['selectHosts'] = self.str2list(sstr=selectHosts)
        if triggerids:
            params['triggerids'] = triggerids
        if groupids:
            params['groupids'] = groupids
        if templateids:
            params['templateids'] = templateids
        if hostids:
            params['hostids'] = hostids
        if itemids:
            params['itemids'] = itemids
        if (para_ext) and (isinstance(para_ext, dict)):
            params = dict(params, **para_ext)
        return self.zbcall(method='trigger.get', params=params)
## ZabbixApi class end -------------------------------------------------------------------------------------------------
