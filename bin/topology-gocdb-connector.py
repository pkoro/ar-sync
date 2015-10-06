#!/usr/bin/python

# Copyright (c) 2013 GRNET S.A., SRCE, IN2P3 CNRS Computing Centre
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of either GRNET S.A., SRCE or IN2P3 CNRS Computing
# Centre
#
# The work represented by this source file is partially funded by
# the EGI-InSPIRE project through the European Commission's 7th
# Framework Programme (contract # INFSO-RI-261323)

import argparse
import copy
import datetime
import httplib
import os
import socket
import sys
import xml.dom.minidom

from OpenSSL.SSL import Error as SSLError
from argo_egi_connectors.config import Global, CustomerConf
from argo_egi_connectors.tools import verify_cert, errmsg_from_excp
from argo_egi_connectors.writers import AvroWriter
from argo_egi_connectors.writers import SingletonLogger as Logger
from exceptions import AssertionError
from urlparse import urlparse


LegMapServType = {'SRM' : 'SRMv2'}
fetchtype = ''

globopts = {}
logger = None

class GOCDBReader:
    def __init__(self, feed, scopes):
        self.gocdbHost = urlparse(feed).netloc
        self.scopes = scopes if scopes else set(['NoScope'])
        self.hostKey = globopts['AuthenticationHostKey'.lower()]
        self.hostCert = globopts['AuthenticationHostCert'.lower()]
        for scope in self.scopes:
            code = "self.serviceList%s = dict(); " % scope
            code += "self.groupList%s = dict();" % scope
            code += "self.siteList%s = dict()" % scope
            exec code
        self.fetched = False

    def getGroupOfServices(self):
        if not self.fetched:
            self.loadDataIfNeeded()

        groups, gl = list(), list()

        for scope in self.scopes:
            code = "gl = gl + [value for key, value in self.groupList%s.iteritems()]" % scope
            exec code

        for d in gl:
            for service in d['services']:
                g = dict()
                g['type'] = fetchtype.upper()
                g['group'] = d['name']
                g['service'] = service['type']
                g['hostname'] = service['hostname']
                g['group_monitored'] = d['monitored']
                g['tags'] = {'scope' : d['scope'], \
                            'monitored' : 1 if service['monitored'] == "Y" else 0, \
                            'production' : 1 if service['production'] == "Y" else 0}
                groups.append(g)

        return groups

    def getGroupOfGroups(self):
        if not self.fetched:
            self.loadDataIfNeeded()

        groupofgroups, gl = list(), list()

        if fetchtype == "ServiceGroups":
            for scope in self.scopes:
                code = "gl = gl + [value for key, value in self.groupList%s.iteritems()]" % scope
                exec code
            for d in gl:
                g = dict()
                g['type'] = 'PROJECT'
                g['group'] = 'EGI'
                g['subgroup'] = d['name']
                g['tags'] = {'monitored' : 1 if d['monitored'] == 'Y' else 0,
                            'scope' : d['scope']}
                groupofgroups.append(g)
        else:
            gg = []
            for scope in self.scopes:
                code = "gg = gg + sorted([value for key, value in self.siteList%s.iteritems()], key=lambda s: s['ngi'])" % scope
                exec code

            for gr in gg:
                g = dict()
                g['type'] = 'NGI'
                g['group'] = gr['ngi']
                g['subgroup'] = gr['site']
                g['tags'] = {'certification' : gr['certification'], \
                             'scope' : gr['scope'], \
                             'infrastructure' : gr['infrastructure']}

                groupofgroups.append(g)

        return groupofgroups

    def getGroupOfEndpoints(self):
        if not self.fetched:
            self.loadDataIfNeeded()

        groupofendpoints, ge = list(), list()
        for scope in self.scopes:
            code = "ge = ge + sorted([value for key, value in self.serviceList%s.iteritems()], key=lambda s: s['site'])" % scope
            exec code

        for gr in ge:
            g = dict()
            g['type'] = fetchtype.upper()
            g['group'] = gr['site']
            g['service'] = gr['type']
            g['hostname'] = gr['hostname']
            g['tags'] = {'scope' : gr['scope'], \
                         'monitored' : 1 if gr['monitored'] == "Y" else 0, \
                         'production' : 1 if gr['production'] == "Y" else 0}
            groupofendpoints.append(g)

        return groupofendpoints

    def loadDataIfNeeded(self):
        try:
            scopequery = "'&scope='+scope"
            for scope in self.scopes:
                eval("self.getSitesInternal(self.siteList%s, %s)" % (scope, '' if scope == 'NoScope' else scopequery))
                eval("self.getServiceGroups(self.groupList%s, %s)" % (scope, '' if scope == 'NoScope' else scopequery))
                eval("self.getServiceEndpoints(self.serviceList%s, %s)" % (scope, '' if scope == 'NoScope' else scopequery))
                self.fetched = True

        except (socket.error, httplib.HTTPException) as e:
            logger.error('Connection to GOCDB failed: ' + str(e))
            raise SystemExit(1)

    def getServiceEndpoints(self, serviceList, scope):
        try:
            if eval(globopts['AuthenticationVerifyServerCert'.lower()]):
                verify_cert(self.gocdbHost, globopts['AuthenticationCAPath'.lower()], 180)
            conn = httplib.HTTPSConnection(self.gocdbHost, 443, self.hostKey, self.hostCert)
            conn.request('GET', '/gocdbpi/private/?method=get_service_endpoint' + scope)
            res = conn.getresponse()
            if res.status == 200:
                doc = xml.dom.minidom.parseString(res.read())
                services = doc.getElementsByTagName('SERVICE_ENDPOINT')
                assert len(services) > 0
                for service in services:
                    serviceId = ''
                    if service.getAttributeNode('PRIMARY_KEY'):
                        serviceId = str(service.attributes['PRIMARY_KEY'].value)
                    if serviceId not in serviceList:
                        serviceList[serviceId] = {}
                    serviceList[serviceId]['hostname'] = service.getElementsByTagName('HOSTNAME')[0].childNodes[0].data
                    serviceList[serviceId]['type'] = service.getElementsByTagName('SERVICE_TYPE')[0].childNodes[0].data
                    serviceList[serviceId]['monitored'] = service.getElementsByTagName('NODE_MONITORED')[0].childNodes[0].data
                    serviceList[serviceId]['production'] = service.getElementsByTagName('IN_PRODUCTION')[0].childNodes[0].data
                    serviceList[serviceId]['site'] = service.getElementsByTagName('SITENAME')[0].childNodes[0].data
                    serviceList[serviceId]['roc'] = service.getElementsByTagName('ROC_NAME')[0].childNodes[0].data
                    serviceList[serviceId]['scope'] = scope.split('=')[1]
                    serviceList[serviceId]['sortId'] = serviceList[serviceId]['hostname'] + '-' + serviceList[serviceId]['type'] + '-' + serviceList[serviceId]['site']
            else:
                logger.error('GOCDBReader.getServiceEndpoints(): HTTP response: %s %s' % (str(res.status), res.reason))
                raise SystemExit(1)
        except AssertionError:
            logger.error("GOCDBReader.getServiceEndpoints(): Error parsing feed")
            raise SystemExit(1)
        except(SSLError, socket.error, socket.timeout) as e:
            logger.error('Connection error %s - %s' % (self.gocdbHost, errmsg_from_excp(e)))
            raise SystemExit(1)

    def getSitesInternal(self, siteList, scope):
        try:
            if eval(globopts['AuthenticationVerifyServerCert'.lower()]):
                verify_cert(self.gocdbHost, globopts['AuthenticationCAPath'.lower()], 180)
            conn = httplib.HTTPSConnection(self.gocdbHost, 443, self.hostKey, self.hostCert)
            conn.request('GET', '/gocdbpi/private/?method=get_site'+scope)
            res = conn.getresponse()
            if res.status == 200:
                dom = xml.dom.minidom.parseString(res.read())
                sites = dom.getElementsByTagName('SITE')
                assert len(sites) > 0
                for site in sites:
                    siteName = site.getAttribute('NAME')
                    if siteName not in siteList:
                        siteList[siteName] = {'site': siteName}
                    siteList[siteName]['infrastructure'] = site.getElementsByTagName('PRODUCTION_INFRASTRUCTURE')[0].childNodes[0].data
                    siteList[siteName]['certification'] = site.getElementsByTagName('CERTIFICATION_STATUS')[0].childNodes[0].data
                    siteList[siteName]['ngi'] = site.getElementsByTagName('ROC')[0].childNodes[0].data
                    siteList[siteName]['scope'] = scope.split('=')[1]
            else:
                logger.error('GOCDBReader.getSitesInternal(): HTTP response: %s %s' % (str(res.status), res.reason))
                raise SystemExit(1)
        except AssertionError:
            logger.error("GOCDBReader.getSitesInternal(): Error parsing feed")
            raise SystemExit(1)
        except(SSLError, socket.error, socket.timeout) as e:
            logger.error('Connection error %s - %s' % (self.gocdbHost, errmsg_from_excp(e)))
            raise SystemExit(1)

    def getServiceGroups(self, groupList, scope):
        try:
            if eval(globopts['AuthenticationVerifyServerCert'.lower()]):
                verify_cert(self.gocdbHost, globopts['AuthenticationCAPath'.lower()], 180)
            conn = httplib.HTTPSConnection(self.gocdbHost, 443, self.hostKey, self.hostCert)
            conn.request('GET', '/gocdbpi/private/?method=get_service_group' + scope)
            res = conn.getresponse()
            if res.status == 200:
                doc = xml.dom.minidom.parseString(res.read())
                groups = doc.getElementsByTagName('SERVICE_GROUP')
                assert len(groups) > 0
                for group in groups:
                    groupId = group.getAttribute('PRIMARY_KEY')
                    if groupId not in groupList:
                        groupList[groupId] = {}
                    groupList[groupId]['name'] = group.getElementsByTagName('NAME')[0].childNodes[0].data
                    groupList[groupId]['monitored'] = group.getElementsByTagName('MONITORED')[0].childNodes[0].data
                    groupList[groupId]['scope'] = scope.split('=')[1]
                    groupList[groupId]['services'] = []
                    services = group.getElementsByTagName('SERVICE_ENDPOINT')
                    for service in services:
                        serviceDict = {}
                        serviceDict['hostname'] = service.getElementsByTagName('HOSTNAME')[0].childNodes[0].data
                        serviceDict['type'] = service.getElementsByTagName('SERVICE_TYPE')[0].childNodes[0].data
                        serviceDict['monitored'] = service.getElementsByTagName('NODE_MONITORED')[0].childNodes[0].data
                        serviceDict['production'] = service.getElementsByTagName('IN_PRODUCTION')[0].childNodes[0].data
                        groupList[groupId]['services'].append(serviceDict)
            else:
                logger.error('GOCDBReader.getServiceGroups(): HTTP response: %s %s' % (str(res.status), res.reason))
                raise SystemExit(1)
        except AssertionError:
            logger.error("GOCDBReader.getServiceGroups(): Error parsing feed")
            raise SystemExit(1)
        except(SSLError, socket.error, socket.timeout) as e:
            logger.error('Connection error %s - %s' % (self.gocdbHost, errmsg_from_excp(e)))
            raise SystemExit(1)

def filter_by_tags(tags, listofelem):
    for attr in tags.keys():
        def getit(elem):
            value = elem['tags'][attr.lower()]
            if isinstance(value, int):
                value = 'Y' if value else 'N'
            if isinstance(tags[attr], list):
                for a in tags[attr]:
                    if value.lower() == a.lower():
                        return True
            else:
                if value.lower() == tags[attr].lower():
                    return True

        listofelem = filter(getit, listofelem)
    return listofelem

def main():
    parser = argparse.ArgumentParser(description="""Fetch entities (ServiceGroups, Sites, Endpoints)
                                                    from GOCDB for every job listed in customer.conf and write them
                                                    in an appropriate place""")
    args = parser.parse_args()
    group_endpoints, group_groups = [], []

    global logger
    logger = Logger(os.path.basename(sys.argv[0]))

    certs = {'Authentication': ['HostKey', 'HostCert', 'CAPath', 'VerifyServerCert']}
    schemas = {'AvroSchemas': ['TopologyGroupOfEndpoints', 'TopologyGroupOfGroups']}
    output = {'Output': ['TopologyGroupOfEndpoints', 'TopologyGroupOfGroups']}
    cglob = Global(certs, schemas, output)
    global globopts
    globopts = cglob.parse()

    confcust = CustomerConf(sys.argv[0])
    confcust.parse()
    confcust.make_dirstruct()
    feeds = confcust.get_mapfeedjobs(sys.argv[0], 'GOCDB', deffeed='https://goc.egi.eu/gocdbpi/')

    timestamp = datetime.datetime.utcnow().strftime('%Y_%m_%d')

    for feed, jobcust in feeds.items():
        scopes = confcust.get_customer_scopes(sys.argv[0], jobcust[0][1] , 'GOCDB' )
        gocdb = GOCDBReader(feed, scopes)

        for job, cust in jobcust:
            jobdir = confcust.get_fulldir(cust, job)
            global fetchtype
            fetchtype = confcust.get_gocdb_fetchtype(job)

            if fetchtype == 'ServiceGroups':
                group_endpoints = gocdb.getGroupOfServices()
            else:
                group_endpoints = gocdb.getGroupOfEndpoints()
            group_groups = gocdb.getGroupOfGroups()

            numge = len(group_endpoints)
            numgg = len(group_groups)

            ggtags = confcust.get_gocdb_ggtags(job)
            if ggtags:
                group_groups = filter_by_tags(ggtags, group_groups)
            filename = jobdir+globopts['OutputTopologyGroupOfGroups'.lower()] % timestamp
            avro = AvroWriter(globopts['AvroSchemasTopologyGroupOfGroups'.lower()], filename,
                            group_groups, os.path.basename(sys.argv[0]))
            avro.write()

            gelegmap = []
            for g in group_endpoints:
                if g['service'] in LegMapServType.keys():
                    gelegmap.append(copy.copy(g))
                    gelegmap[-1]['service'] = LegMapServType[g['service']]
            getags = confcust.get_gocdb_getags(job)
            numgeleg = len(gelegmap)
            if getags:
                group_endpoints = filter_by_tags(getags, group_endpoints)
                gelegmap = filter_by_tags(getags, gelegmap)
            filename = jobdir+globopts['OutputTopologyGroupOfEndpoints'.lower()] % timestamp
            avro = AvroWriter(globopts['AvroSchemasTopologyGroupOfEndpoints'.lower()], filename,
                            group_endpoints + gelegmap, os.path.basename(sys.argv[0]))
            avro.write()

            logger.info('Job:'+job+' Fetched Endpoints:%d' % (numge + numgeleg) +' Groups(%s):%d' % (fetchtype, numgg))
            if getags or ggtags:
                selstr = 'Job:%s Selected ' % (job)
                selge, selgg = '', ''
                if getags:
                    for key, value in getags.items():
                        if isinstance(value, list):
                            value = '['+','.join(value)+']'
                        selge += '%s:%s,' % (key, value)
                    selstr += 'Endpoints(%s):' % selge[:len(selge) - 1]
                    selstr += '%d ' % (len(group_endpoints) + len(gelegmap))
                if ggtags:
                    for key, value in ggtags.items():
                        if isinstance(value, list):
                            value = '['+','.join(value)+']'
                        selgg += '%s:%s,' % (key, value)
                    selstr += 'Groups(%s):' % selgg[:len(selgg) - 1]
                    selstr += '%d' % (len(group_groups))

                logger.info(selstr)
main()
