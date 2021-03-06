# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Zadara Storage Inc.
# Copyright (c) 2011 OpenStack LLC.
# Copyright 2011 University of Southern California
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
"""
Unit Tests for volume types extra specs code
"""

from cinder import context
from cinder import db
from cinder import exception
from cinder import test


class VolumeGlanceMetadataTestCase(test.TestCase):

    def setUp(self):
        super(VolumeGlanceMetadataTestCase, self).setUp()
        self.context = context.get_admin_context()

    def tearDown(self):
        super(VolumeGlanceMetadataTestCase, self).tearDown()

    def test_vol_glance_metadata_bad_vol_id(self):
        ctxt = context.get_admin_context()
        self.assertRaises(exception.VolumeNotFound,
                          db.volume_glance_metadata_create,
                          ctxt, 1, 'key1', 'value1')
        self.assertRaises(exception.VolumeNotFound,
                          db.volume_glance_metadata_get, ctxt, 1)
        db.volume_glance_metadata_delete_by_volume(ctxt, 10)

    def test_vol_update_glance_metadata(self):
        ctxt = context.get_admin_context()
        db.volume_create(ctxt, {'id': 1})
        db.volume_create(ctxt, {'id': 2})
        vol_metadata = db.volume_glance_metadata_create(ctxt, 1, 'key1',
                                                        'value1')
        vol_metadata = db.volume_glance_metadata_create(ctxt, 2, 'key1',
                                                        'value1')
        vol_metadata = db.volume_glance_metadata_create(ctxt, 2,
                                                        'key2',
                                                        'value2')

        expected_metadata_1 = {'volume_id': '1',
                               'key': 'key1',
                               'value': 'value1'}

        metadata = db.volume_glance_metadata_get(ctxt, 1)
        self.assertEqual(len(metadata), 1)
        for key, value in expected_metadata_1.items():
            self.assertEqual(metadata[0][key], value)

        expected_metadata_2 = ({'volume_id': '2',
                                'key': 'key1',
                                'value': 'value1'},
                               {'volume_id': '2',
                                'key': 'key2',
                                'value': 'value2'})

        metadata = db.volume_glance_metadata_get(ctxt, 2)
        self.assertEqual(len(metadata), 2)
        for expected, meta in zip(expected_metadata_2, metadata):
            for key, value in expected.iteritems():
                self.assertEqual(meta[key], value)

        self.assertRaises(exception.GlanceMetadataExists,
                          db.volume_glance_metadata_create,
                          ctxt, 1, 'key1', 'value1a')

        metadata = db.volume_glance_metadata_get(ctxt, 1)
        self.assertEqual(len(metadata), 1)
        for key, value in expected_metadata_1.items():
            self.assertEqual(metadata[0][key], value)

    def test_vol_delete_glance_metadata(self):
        ctxt = context.get_admin_context()
        db.volume_create(ctxt, {'id': 1})
        db.volume_glance_metadata_delete_by_volume(ctxt, 1)
        vol_metadata = db.volume_glance_metadata_create(ctxt, 1, 'key1',
                                                        'value1')
        db.volume_glance_metadata_delete_by_volume(ctxt, 1)
        metadata = db.volume_glance_metadata_get(ctxt, 1)
        self.assertEqual(len(metadata), 0)
        db.volume_glance_metadata_delete_by_volume(ctxt, 1)
        metadata = db.volume_glance_metadata_get(ctxt, 1)
        self.assertEqual(len(metadata), 0)

    def test_vol_glance_metadata_copy_to_snapshot(self):
        ctxt = context.get_admin_context()
        db.volume_create(ctxt, {'id': 1})
        db.snapshot_create(ctxt, {'id': 100, 'volume_id': 1})
        vol_meta = db.volume_glance_metadata_create(ctxt, 1, 'key1',
                                                    'value1')
        db.volume_glance_metadata_copy_to_snapshot(ctxt, 100, 1)

        expected_meta = {'snapshot_id': '100',
                         'key': 'key1',
                         'value': 'value1'}

        for meta in db.volume_snapshot_glance_metadata_get(ctxt, 100):
            for (key, value) in expected_meta.items():
                self.assertEquals(meta[key], value)
