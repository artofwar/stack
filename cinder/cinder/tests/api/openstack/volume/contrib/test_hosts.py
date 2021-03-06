# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 OpenStack, LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime

from lxml import etree
import webob.exc

from cinder.api.openstack.volume.contrib import hosts as os_hosts
from cinder import context
from cinder import db
from cinder import flags
from cinder.openstack.common import log as logging
from cinder.openstack.common import timeutils
from cinder import test


FLAGS = flags.FLAGS
LOG = logging.getLogger(__name__)
created_time = datetime.datetime(2012, 11, 14, 1, 20, 41, 95099)
curr_time = timeutils.utcnow()

SERVICE_LIST = [
    {'created_at': created_time, 'updated_at': curr_time,
     'host': 'test.host.1', 'topic': 'cinder-volume', 'disabled': 0,
     'availability_zone': 'cinder'},
    {'created_at': created_time, 'updated_at': curr_time,
     'host': 'test.host.1', 'topic': 'cinder-volume', 'disabled': 0,
     'availability_zone': 'cinder'},
    {'created_at': created_time, 'updated_at': curr_time,
     'host': 'test.host.1', 'topic': 'cinder-volume', 'disabled': 0,
     'availability_zone': 'cinder'},
    {'created_at': created_time, 'updated_at': curr_time,
     'host': 'test.host.1', 'topic': 'cinder-volume', 'disabled': 0,
     'availability_zone': 'cinder'}]

LIST_RESPONSE = [{'service-status': 'available', 'service': 'cinder-volume',
                  'zone': 'cinder', 'service-state': 'enabled',
                  'host_name': 'test.host.1', 'last-update': curr_time},
                 {'service-status': 'available', 'service': 'cinder-volume',
                  'zone': 'cinder', 'service-state': 'enabled',
                  'host_name': 'test.host.1', 'last-update': curr_time},
                 {'service-status': 'available', 'service': 'cinder-volume',
                  'zone': 'cinder', 'service-state': 'enabled',
                  'host_name': 'test.host.1', 'last-update': curr_time},
                 {'service-status': 'available', 'service': 'cinder-volume',
                  'zone': 'cinder', 'service-state': 'enabled',
                  'host_name': 'test.host.1', 'last-update': curr_time}]


def stub_service_get_all(self, req):
    return SERVICE_LIST


class FakeRequest(object):
    environ = {'cinder.context': context.get_admin_context()}
    GET = {}


class FakeRequestWithcinderZone(object):
    environ = {'cinder.context': context.get_admin_context()}
    GET = {'zone': 'cinder'}


class HostTestCase(test.TestCase):
    """Test Case for hosts."""

    def setUp(self):
        super(HostTestCase, self).setUp()
        self.controller = os_hosts.HostController()
        self.req = FakeRequest()
        self.stubs.Set(db, 'service_get_all',
                       stub_service_get_all)

    def _test_host_update(self, host, key, val, expected_value):
        body = {key: val}
        result = self.controller.update(self.req, host, body=body)
        self.assertEqual(result[key], expected_value)

    def test_list_hosts(self):
        """Verify that the volume hosts are returned."""
        hosts = os_hosts._list_hosts(self.req)
        self.assertEqual(hosts, LIST_RESPONSE)

        cinder_hosts = os_hosts._list_hosts(self.req, 'cinder-volume')
        expected = [host for host in LIST_RESPONSE
                    if host['service'] == 'cinder-volume']
        self.assertEqual(cinder_hosts, expected)

    def test_list_hosts_with_zone(self):
        req = FakeRequestWithcinderZone()
        hosts = os_hosts._list_hosts(req)
        self.assertEqual(hosts, LIST_RESPONSE)

    def test_bad_status_value(self):
        self.assertRaises(webob.exc.HTTPBadRequest, self.controller.update,
                          self.req, 'test.host.1', body={'status': 'bad'})
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.update,
                          self.req,
                          'test.host.1',
                          body={'status': 'disablabc'})

    def test_bad_update_key(self):
        bad_body = {'crazy': 'bad'}
        self.assertRaises(webob.exc.HTTPBadRequest, self.controller.update,
                          self.req, 'test.host.1', body=bad_body)

    def test_bad_update_key_and_correct_udpate_key(self):
        bad_body = {'status': 'disable', 'crazy': 'bad'}
        self.assertRaises(webob.exc.HTTPBadRequest, self.controller.update,
                          self.req, 'test.host.1', body=bad_body)

    def test_good_udpate_keys(self):
        body = {'status': 'disable'}
        self.assertRaises(NotImplementedError, self.controller.update,
                          self.req, 'test.host.1', body=body)

    def test_bad_host(self):
        self.assertRaises(webob.exc.HTTPNotFound,
                          self.controller.update,
                          self.req,
                          'bogus_host_name',
                          body={'disabled': 0})

    def test_show_forbidden(self):
        self.req.environ['cinder.context'].is_admin = False
        dest = 'dummydest'
        self.assertRaises(webob.exc.HTTPForbidden,
                          self.controller.show,
                          self.req, dest)
        self.req.environ['cinder.context'].is_admin = True

    def test_show_host_not_exist(self):
        """A host given as an argument does not exists."""
        self.req.environ['cinder.context'].is_admin = True
        dest = 'dummydest'
        self.assertRaises(webob.exc.HTTPNotFound,
                          self.controller.show,
                          self.req, dest)


class HostSerializerTest(test.TestCase):
    def setUp(self):
        super(HostSerializerTest, self).setUp()
        self.deserializer = os_hosts.HostDeserializer()

    def test_index_serializer(self):
        serializer = os_hosts.HostIndexTemplate()
        text = serializer.serialize(SERVICE_LIST)

        tree = etree.fromstring(text)

        self.assertEqual('hosts', tree.tag)
        self.assertEqual(len(SERVICE_LIST), len(tree))
        for i in range(len(SERVICE_LIST)):
            self.assertEqual('host', tree[i].tag)
            self.assertEqual(SERVICE_LIST[i]['host'],
                             tree[i].get('host'))
            self.assertEqual(SERVICE_LIST[i]['topic'],
                             tree[i].get('topic'))

    def test_update_serializer_with_status(self):
        exemplar = dict(host='test.host.1', status='enabled')
        serializer = os_hosts.HostUpdateTemplate()
        text = serializer.serialize(exemplar)

        tree = etree.fromstring(text)

        self.assertEqual('host', tree.tag)
        for key, value in exemplar.items():
            self.assertEqual(value, tree.get(key))

    def test_update_deserializer(self):
        exemplar = dict(status='enabled', foo='bar')
        intext = ("<?xml version='1.0' encoding='UTF-8'?>\n"
                  '<updates><status>enabled</status><foo>bar</foo></updates>')
        result = self.deserializer.deserialize(intext)

        self.assertEqual(dict(body=exemplar), result)
