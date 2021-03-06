from novaclient import exceptions
from novaclient.v1_1 import flavors
from tests import utils
from tests.v1_1 import fakes


cs = fakes.FakeClient()


class FlavorsTest(utils.TestCase):

    def test_list_flavors(self):
        fl = cs.flavors.list()
        cs.assert_called('GET', '/flavors/detail')
        [self.assertTrue(isinstance(f, flavors.Flavor)) for f in fl]

    def test_list_flavors_undetailed(self):
        fl = cs.flavors.list(detailed=False)
        cs.assert_called('GET', '/flavors')
        [self.assertTrue(isinstance(f, flavors.Flavor)) for f in fl]

    def test_get_flavor_details(self):
        f = cs.flavors.get(1)
        cs.assert_called('GET', '/flavors/1')
        self.assertTrue(isinstance(f, flavors.Flavor))
        self.assertEqual(f.ram, 256)
        self.assertEqual(f.disk, 10)
        self.assertEqual(f.ephemeral, 10)
        self.assertEqual(f.is_public, True)

    def test_get_flavor_details_diablo(self):
        f = cs.flavors.get(3)
        cs.assert_called('GET', '/flavors/3')
        self.assertTrue(isinstance(f, flavors.Flavor))
        self.assertEqual(f.ram, 256)
        self.assertEqual(f.disk, 10)
        self.assertEqual(f.ephemeral, 'N/A')
        self.assertEqual(f.is_public, 'N/A')

    def test_find(self):
        f = cs.flavors.find(ram=256)
        cs.assert_called('GET', '/flavors/detail')
        self.assertEqual(f.name, '256 MB Server')

        f = cs.flavors.find(disk=20)
        self.assertEqual(f.name, '512 MB Server')

        self.assertRaises(exceptions.NotFound, cs.flavors.find, disk=12345)

    def test_create(self):
        f = cs.flavors.create("flavorcreate", 512, 1, 10, 1234, ephemeral=10,
                              is_public=False)

        body = {
            "flavor": {
                "name": "flavorcreate",
                "ram": 512,
                "vcpus": 1,
                "disk": 10,
                "OS-FLV-EXT-DATA:ephemeral": 10,
                "id": 1234,
                "swap": 0,
                "rxtx_factor": 1,
                "os-flavor-access:is_public": False,
            }
        }

        cs.assert_called('POST', '/flavors', body)
        self.assertTrue(isinstance(f, flavors.Flavor))

    def test_create_ephemeral_ispublic_defaults(self):
        f = cs.flavors.create("flavorcreate", 512, 1, 10, 1234)

        body = {
            "flavor": {
                "name": "flavorcreate",
                "ram": 512,
                "vcpus": 1,
                "disk": 10,
                "OS-FLV-EXT-DATA:ephemeral": 0,
                "id": 1234,
                "swap": 0,
                "rxtx_factor": 1,
                "os-flavor-access:is_public": True,
            }
        }

        cs.assert_called('POST', '/flavors', body)
        self.assertTrue(isinstance(f, flavors.Flavor))

    def test_invalid_parameters_create(self):
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", "invalid", 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, "invalid", 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor=1, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, "invalid", 1234, swap=0,
                          ephemeral=0, rxtx_factor=1, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, "invalid", swap=0,
                          ephemeral=0, rxtx_factor=1, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap="invalid",
                          ephemeral=0, rxtx_factor=1, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral="invalid", rxtx_factor=1, is_public=True)
        self.assertRaises(exceptions.CommandError, cs.flavors.create,
                          "flavorcreate", 512, 1, 10, 1234, swap=0,
                          ephemeral=0, rxtx_factor="invalid", is_public=True)

    def test_delete(self):
        cs.flavors.delete("flavordelete")
        cs.assert_called('DELETE', '/flavors/flavordelete')

    def test_set_keys(self):
        f = cs.flavors.get(1)
        f.set_keys({'k1': 'v1'})
        cs.assert_called('POST', '/flavors/1/os-extra_specs',
                         {"extra_specs": {'k1': 'v1'}})

    def test_unset_keys(self):
        f = cs.flavors.get(1)
        f.unset_keys(['k1'])
        cs.assert_called('DELETE', '/flavors/1/os-extra_specs/k1')
