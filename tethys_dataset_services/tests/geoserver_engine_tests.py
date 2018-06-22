import os
import random
import string
import unittest
import mock
import geoserver

from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine

try:
    from tethys_dataset_services.tests.test_config import TEST_GEOSERVER_DATASET_SERVICE

except ImportError:
    print('ERROR: To perform tests, you must create a file in the "tests" package called "test_config.py". In this file'
          'provide a dictionary called "TEST_GEOSERVER_DATASET_SERVICE" with keys "ENDPOINT", "USERNAME", and '
          '"PASSWORD".')
    exit(1)


def random_string_generator(size):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))


def pause(seconds):
    # Pause
    for i in range(0, 10000 * seconds):
        pass


def mock_get_style(name, workspace=None):
    mock_style = mock.NonCallableMagicMock(workspace=workspace)
    mock_style.name = name
    return mock_style


class TestGeoServerDatasetEngine(unittest.TestCase):

    def setUp(self):
        # Globals
        self.debug = False

        # Files
        self.tests_root = os.path.abspath(os.path.dirname(__file__))
        self.files_root = os.path.join(self.tests_root, 'files')
        self.shapefile_name = 'test'
        self.shapefile_base = os.path.join(self.files_root, 'shapefile', self.shapefile_name)

        # Create Test Engine
        self.engine = GeoServerSpatialDatasetEngine(endpoint=TEST_GEOSERVER_DATASET_SERVICE['ENDPOINT'],
                                                    username=TEST_GEOSERVER_DATASET_SERVICE['USERNAME'],
                                                    password=TEST_GEOSERVER_DATASET_SERVICE['PASSWORD'])

        # Catalog
        self.catalog_endpoint = 'http://localhost:8181/geoserver/'
        self.mock_catalog = mock.NonCallableMagicMock(gs_base_url=self.catalog_endpoint)

        # Mock Objects
        self.workspace_name = 'a-workspace'

        # Store
        self.store_name = 'a-store'
        self.mock_store = mock.NonCallableMagicMock()  #: Needs to pass not callable test
        # the "name" attribute needs to be set after create b/c name is a constructor argument
        # http://blog.tunarob.com/2017/04/27/mock-name-attribute/
        self.mock_store.name = self.store_name

        # Default Style
        self.default_style_name = 'a-style'
        self.mock_default_style = mock.NonCallableMagicMock(workspace=self.workspace_name)
        self.mock_default_style.name = self.default_style_name

        # Styles
        self.style_names = ['points', 'lines']
        self.mock_styles = []
        for sn in self.style_names:
            mock_style = mock.NonCallableMagicMock(workspace=self.workspace_name)
            mock_style.name = sn
            self.mock_styles.append(mock_style)

        # Resources
        self.resource_names = ['foo', 'bar', 'goo']
        self.mock_resources = []
        for rn in self.resource_names:
            mock_resource = mock.NonCallableMagicMock(workspace=self.workspace_name)
            mock_resource.name = rn
            mock_resource.store = self.mock_store
            self.mock_resources.append(mock_resource)

        # Layers
        self.layer_names = ['baz', 'bat', 'jazz']
        self.mock_layers = []
        for ln in self.layer_names:
            mock_layer = mock.NonCallableMagicMock(workspace=self.workspace_name)
            mock_layer.name = ln
            mock_layer.store = self.mock_store
            mock_layer.default_style = self.mock_default_style
            mock_layer.styles = self.mock_styles
            self.mock_layers.append(mock_layer)

        # Layer groups
        self.layer_group_names = ['boo', 'moo']
        self.mock_layer_groups = []
        for lgn in self.layer_group_names:
            mock_layer_group = mock.NonCallableMagicMock(
                workspace=self.workspace_name,
                catalog=self.mock_catalog,
                dom='fake-dom',
                layers=self.layer_names
            )
            mock_layer_group.name = lgn
            self.mock_layer_groups.append(mock_layer_group)

        # # Create Test Workspaces
        # # self.test_resource_workspace = random_string_generator(10)
        # self.test_resource_workspace = random_string_generator(10)
        # self.engine.create_workspace(workspace_id=self.test_resource_workspace, uri=random_string_generator(5))
        #
        # # Create Test Stores/Resources/Layers
        # # Shapefile
        #
        # # Store name
        # self.test_resource_store = random_string_generator(10)
        #
        # # Resource and Layer will take the name of the file
        # self.test_resource_name = self.test_resource_store
        # self.test_layer_name = self.test_resource_store
        #
        # # Identifiers of the form 'workspace:item'
        # self.test_store_identifier = '{0}:{1}'.format(self.test_resource_workspace, self.test_resource_store)
        # self.test_resource_identifier = '{0}:{1}'.format(self.test_resource_workspace, self.test_resource_name)
        #
        # # Do create shapefile
        # self.engine.create_shapefile_resource(self.test_store_identifier, shapefile_base=self.shapefile_base,
        #                                       overwrite=True)
        #
        # # Coverage
        #
        # # Create Test Style
        # self.test_style_name = 'point'
        #
        # # Create Test Layer Groups
        # self.test_layer_group_name = random_string_generator(10)
        # self.engine.create_layer_group(layer_group_id=self.test_layer_group_name,
        #                                layers=(self.test_layer_name,),
        #                                styles=(self.test_style_name,))
        #
        # # Pause
        # pause(10)
        pass

    def tearDown(self):
        # # Delete test layer groups
        # self.engine.delete_layer_group(layer_group_id=self.test_layer_group_name)
        #
        # # Delete test resources & layers
        # self.engine.delete_resource(self.test_resource_identifier, recurse=True)
        #
        # # Delete stores
        # self.engine.delete_store(self.test_store_identifier)
        #
        # # Delete test workspace
        # self.engine.delete_workspace(self.test_resource_workspace)
        pass

    def assert_valid_response_object(self, response_object):
        # Response object should be a dictionary with the keys 'success' and either 'result' if success is True
        # or 'error' if success is False
        self.assertIsInstance(response_object, dict)
        self.assertIn('success', response_object)

        if isinstance(response_object, dict) and 'success' in response_object:
            if response_object['success'] is True:
                self.assertIn('result', response_object)
            elif response_object['success'] is False:
                self.assertIn('error', response_object)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_resources(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resources.return_value = self.mock_resources

        # Execute
        response = self.engine.list_resources(debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Returns list
        self.assertIsInstance(result, list)

        # List of strings
        if len(result) > 0:
            self.assertIsInstance(result[0], str)

        # Test layer listed
        for n in self.resource_names:
            self.assertIn(n, result)

        mc.get_resources.called_with(store=None, workspace=None)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_resources_with_properties(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resources.return_value = self.mock_resources

        # Execute
        response = self.engine.list_resources(with_properties=True)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Returns list
        self.assertIsInstance(result, list)

        # List of dictionaries
        if len(result) > 0:
            self.assertIsInstance(result[0], dict)

        for r in result:
            self.assertIn('name', r)
            self.assertIn(r['name'], self.resource_names)
            self.assertIn('workspace', r)
            self.assertEqual(self.workspace_name, r['workspace'])
            self.assertIn('store', r)
            self.assertEqual(self.store_name, r['store'])

        mc.get_resources.called_with(store=None, workspace=None)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_resources_ambiguous_error(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resources.side_effect = geoserver.catalog.AmbiguousRequestError()

        # Execute
        response = self.engine.list_resources(with_properties=True)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertFalse(response['success'])

        mc.get_resources.called_with(store=None, workspace=None)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_resources_multiple_stores_error(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resources.side_effect = TypeError()

        # Execute
        response = self.engine.list_resources(with_properties=True)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertFalse(response['success'])
        self.assertIn('Multiple stores found named', response['error'])

        mc.get_resources.called_with(store=None, workspace=None)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_layers(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layers.return_value = self.mock_layers

        # Execute
        response = self.engine.list_layers(debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Returns list
        self.assertIsInstance(result, list)

        # List of strings
        if len(result) > 0:
            self.assertIsInstance(result[0], str)

        # Test layer listed
        for n in self.layer_names:
            self.assertIn(n, result)

        mc.get_layers.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_layers_with_properties(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layers.return_value = self.mock_layers

        # Execute
        response = self.engine.list_layers(with_properties=True)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Returns list
        self.assertIsInstance(result, list)

        # List of dictionaries
        if len(result) > 0:
            self.assertIsInstance(result[0], dict)

        for r in result:
            self.assertIn('name', r)
            self.assertIn(r['name'], self.layer_names)
            self.assertIn('workspace', r)
            self.assertEqual(self.workspace_name, r['workspace'])
            self.assertIn('store', r)
            self.assertEqual(self.store_name, r['store'])
            self.assertIn('default_style', r)
            w_default_style = '{}:{}'.format(self.workspace_name, self.default_style_name)
            self.assertEqual(w_default_style, r['default_style'])
            self.assertIn('styles', r)
            w_styles = ['{}:{}'.format(self.workspace_name, style) for style in self.style_names]
            for s in r['styles']:
                self.assertIn(s, w_styles)

        mc.get_layers.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_layer_groups(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layergroups.return_value = self.mock_layer_groups

        # Execute
        response = self.engine.list_layer_groups(debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # List of strings
        if len(result) > 0:
            self.assertIsInstance(result[0], str)

        # Test layer group listed
        for r in result:
            self.assertIn(r, self.layer_group_names)

        mc.get_layergroups.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_list_layer_groups_with_properties(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layergroups.return_value = self.mock_layer_groups

        # Execute
        response = self.engine.list_layer_groups(with_properties=True, debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Returns list
        self.assertIsInstance(result, list)

        # List of dictionaries
        if len(result) > 0:
            self.assertIsInstance(result[0], dict)

        for r in result:
            self.assertIn('name', r)
            self.assertIn(r['name'], self.layer_group_names)
            self.assertIn('workspace', r)
            self.assertEqual(self.workspace_name, r['workspace'])
            self.assertIn('catalog', r)
            self.assertEqual(self.catalog_endpoint, r['catalog'])
            self.assertIn('layers', r)
            self.assertEqual(self.layer_names, r['layers'])
            self.assertNotIn('dom', r)

        mc.get_layergroups.assert_called()

    def test_list_workspaces(self):
        raise NotImplementedError()

    def test_list_stores(self):
        raise NotImplementedError()

    def test_list_styles(self):
        raise NotImplementedError()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_get_resource(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = self.mock_resources[0]

        # Execute
        response = self.engine.get_resource(resource_id=self.resource_names[0], debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Properties
        self.assertIn('name', r)
        self.assertIn(r['name'], self.resource_names)
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])
        self.assertIn('store', r)
        self.assertEqual(self.store_name, r['store'])

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=None)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_get_resource_with_workspace(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = self.mock_resources[0]

        # Execute
        resource_id = self.workspace_name + ":" + self.resource_names[0]
        response = self.engine.get_resource(resource_id=resource_id,
                                            debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Properties
        self.assertIn('name', r)
        self.assertIn(r['name'], self.resource_names)
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])
        self.assertIn('store', r)
        self.assertEqual(self.store_name, r['store'])

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=self.workspace_name)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_get_resource_none(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = None

        # Execute
        response = self.engine.get_resource(resource_id=self.resource_names[0], debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # False
        self.assertFalse(response['success'])

        # Expect Error
        r = response['error']

        # Properties
        self.assertIn('not found', r)

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=None)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_get_resource_failed_request_error(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.side_effect = geoserver.catalog.FailedRequestError('Failed Request')

        # Execute
        response = self.engine.get_resource(resource_id=self.resource_names[0], debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # False
        self.assertFalse(response['success'])

        # Expect Error
        r = response['error']

        # Properties
        self.assertIn('Failed Request', r)

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=None)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_get_resource_with_store(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = self.mock_resources[0]

        # Execute
        resource_id = self.workspace_name + ":" + self.resource_names[0]
        response = self.engine.get_resource(resource_id=resource_id,
                                            store=self.store_name,
                                            debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Properties
        self.assertIn('name', r)
        self.assertIn(r['name'], self.resource_names)
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])
        self.assertIn('store', r)
        self.assertEqual(self.store_name, r['store'])

        mc.get_resource.assert_called_with(name=self.resource_names[0],
                                           store=self.store_name,
                                           workspace=self.workspace_name)

    def test_get_resource_multiple_with_name(self):
        raise NotImplementedError()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_get_layer(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layer.return_value = self.mock_layers[0]

        # Execute
        response = self.engine.get_layer(layer_id=self.layer_names[0], debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Properties
        self.assertIn('name', r)
        self.assertEqual(self.layer_names[0], r['name'])
        self.assertIn('store', r)
        self.assertEqual(self.store_name, r['store'])
        self.assertIn('default_style', r)
        self.assertIn(self.default_style_name, r['default_style'])
        self.assertIn('styles', r)
        w_styles = ['{}:{}'.format(self.workspace_name, style) for style in self.style_names]
        for s in r['styles']:
            self.assertIn(s, w_styles)

        mc.get_layer.assert_called_with(name=self.layer_names[0])

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_get_layer_group(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layergroup.return_value = self.mock_layer_groups[0]

        # Execute
        response = self.engine.get_layer_group(layer_group_id=self.layer_group_names[0], debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # List of dictionaries
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])
        self.assertIn('catalog', r)
        self.assertEqual(self.catalog_endpoint, r['catalog'])
        self.assertIn('layers', r)
        self.assertEqual(self.layer_names, r['layers'])
        self.assertNotIn('dom', r)

        mc.get_layergroup.assert_called_with(name=self.layer_group_names[0])

    def test_get_store(self):
        raise NotImplementedError()

    def test_get_workspace(self):
        raise NotImplementedError()

    def test_get_style(self):
        raise NotImplementedError()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_resource(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = mock.NonCallableMagicMock(
            title='foo',
            geometry='points'
        )

        # Setup
        resource_id = self.workspace_name + ":" + self.resource_names[0]
        new_title = random_string_generator(15)
        new_geometry = 'lines'

        # Execute
        response = self.engine.update_resource(resource_id=resource_id,
                                               title=new_title,
                                               geometry=new_geometry,
                                               debug=self.debug)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Properties
        self.assertEqual(result['title'], new_title)
        self.assertEqual(result['geometry'], new_geometry)

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=self.workspace_name)
        mc.save.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_resource_style(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = mock.NonCallableMagicMock(
            styles=['style_name'],
        )
        mc.get_style.side_effect = mock_get_style

        # Setup
        resource_id = self.workspace_name + ":" + self.resource_names[0]
        new_styles = ['new_style_name']

        # Execute
        response = self.engine.update_resource(resource_id=resource_id,
                                               styles=new_styles,
                                               debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Properties
        self.assertEqual(result['styles'], new_styles)

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=self.workspace_name)
        mc.save.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_resource_style_colon(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = mock.NonCallableMagicMock(
            styles=['1:2'],
        )
        mc.get_style.side_effect = mock_get_style

        # Setup
        resource_id = self.workspace_name + ":" + self.resource_names[0]
        new_styles = ['11:22']

        # Execute
        response = self.engine.update_resource(resource_id=resource_id,
                                               styles=new_styles,
                                               debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Properties
        self.assertEqual(result['styles'], new_styles)

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=self.workspace_name)
        mc.save.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_resource_failed_request_error(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.side_effect = geoserver.catalog.FailedRequestError('Failed Request')

        # Setup
        resource_id = self.workspace_name + ":" + self.resource_names[0]
        new_title = random_string_generator(15)
        new_geometry = 'lines'

        # Execute
        response = self.engine.update_resource(resource_id=resource_id,
                                               title=new_title,
                                               geometry=new_geometry,
                                               debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Fail
        self.assertFalse(response['success'])

        # Expect Error
        r = response['error']

        # Properties
        self.assertIn('Failed Request', r)

        mc.get_resource.assert_called_with(name=self.resource_names[0], store=None, workspace=self.workspace_name)

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_resource_store(self, mock_catalog):
        mc = mock_catalog()
        mc.get_resource.return_value = mock.NonCallableMagicMock(
            store=self.store_name,
            title='foo',
            geometry='points'
        )

        # Setup
        resource_id = self.workspace_name + ":" + self.resource_names[0]
        new_title = random_string_generator(15)
        new_geometry = 'lines'

        # Execute
        response = self.engine.update_resource(resource_id=resource_id,
                                               store=self.store_name,
                                               title=new_title,
                                               geometry=new_geometry,
                                               debug=self.debug)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Properties
        self.assertEqual(result['title'], new_title)
        self.assertEqual(result['geometry'], new_geometry)
        self.assertEqual(result['store'], self.store_name)

        mc.get_resource.assert_called_with(name=self.resource_names[0],
                                           store=self.store_name,
                                           workspace=self.workspace_name)
        mc.save.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_layer(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layer.return_value = mock.NonCallableMagicMock(
            name=self.layer_names[0],
            title='foo',
            geometry='points'
        )

        # Setup
        new_title = random_string_generator(15)
        new_geometry = 'lines'

        # Execute
        response = self.engine.update_layer(layer_id=self.layer_names[0],
                                            title=new_title,
                                            geometry=new_geometry,
                                            debug=self.debug)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Properties
        self.assertEqual(result['title'], new_title)
        self.assertEqual(result['geometry'], new_geometry)

        mc.get_layer.assert_called_with(name=self.layer_names[0])
        mc.save.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_layer_group(self, mock_catalog):
        mc = mock_catalog()
        mock_layer_group = mock.NonCallableMagicMock(
            layers=self.layer_names
        )
        mock_layer_group.name = self.layer_group_names[0]
        mc.get_layergroup.return_value = mock_layer_group

        # Setup
        new_layers = random_string_generator(15)

        # Execute
        response = self.engine.update_layer_group(layer_group_id=self.layer_group_names[0],
                                                  layers=new_layers,
                                                  debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # Properties
        self.assertEqual(result['layers'], new_layers)

        mc.get_layergroup.assert_called_with(name=self.layer_group_names[0])
        mc.save.assert_called()

    @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    def test_update_layer_group_failed_request_error(self, mock_catalog):
        mc = mock_catalog()
        mc.get_layergroup.side_effect = geoserver.catalog.FailedRequestError('Failed Request')

        # Setup
        new_layers = random_string_generator(15)

        # Execute
        response = self.engine.update_layer_group(layer_group_id=self.mock_layer_groups[0],
                                                  layers=new_layers,
                                                  debug=self.debug)

        # Validate response object
        self.assert_valid_response_object(response)

        # Fail
        self.assertFalse(response['success'])

        # Expect Error
        r = response['error']

        # Properties
        self.assertIn('Failed Request', r)

        mc.get_layergroup.assert_called_with(name=self.mock_layer_groups[0])

    def test_delete_resource(self):
        # Must delete layer group and layer first
        self.engine.delete_layer_group(layer_group_id=self.test_layer_group_name)
        self.engine.delete_layer(layer_id=self.test_layer_name)

        # Do delete
        response = self.engine.delete_resource(resource_id=self.test_resource_identifier)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        self.assertIsNone(response['result'])

    def test_delete_resource_belongs_to_layer(self):
        # Do delete without deleting layer group and layer
        response = self.engine.delete_resource(resource_id=self.test_resource_identifier)

        # Should fail
        self.assert_valid_response_object(response)
        self.assertFalse(response['success'])

    def test_delete_resource_recurse(self):
        # Force delete with recurse
        response = self.engine.delete_resource(resource_id=self.test_resource_identifier, recurse=True)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        self.assertIsNone(response['result'])

    def test_delete_resource_does_not_exist(self):
        # Do delete
        response = self.engine.delete_resource(resource_id='iDontExist')

        # Should fail
        self.assert_valid_response_object(response)
        self.assertFalse(response['success'])

    def test_delete_layer(self):
        # Delete layer group first
        self.engine.delete_layer_group(layer_group_id=self.test_layer_group_name)

        # Do delete
        response = self.engine.delete_layer(layer_id=self.test_layer_name)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        self.assertIsNone(response['result'])

    def test_delete_layer_belongs_to_group(self):
        # Do delete without deleting layer group
        response = self.engine.delete_layer(layer_id=self.test_layer_name)

        # Should fail
        self.assert_valid_response_object(response)
        self.assertFalse(response['success'])

    def test_delete_layer_recurse(self):
        # Force delete with recurse
        response = self.engine.delete_layer(layer_id=self.test_layer_name, recurse=True)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        self.assertIsNone(response['result'])

    def test_delete_layer_does_not_exist(self):
        # Delete layer group first
        self.engine.delete_layer_group(layer_group_id=self.test_layer_group_name)

        # Do delete
        response = self.engine.delete_layer(layer_id='iDontExist')

        # Should fail
        self.assert_valid_response_object(response)
        self.assertFalse(response['success'])

    def test_delete_layer_group(self):
        # Do delete
        response = self.engine.delete_layer_group(layer_group_id=self.test_layer_group_name)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        self.assertIsNone(response['result'])

    def test_delete_layer_group_does_not_exist(self):
        # Do delete
        response = self.engine.delete_layer_group(layer_group_id='iDontExist')

        # Should fail
        self.assert_valid_response_object(response)
        self.assertFalse(response['success'])

    def test_delete_workspace(self):
        raise NotImplementedError()

    def test_delete_store(self):
        raise NotImplementedError()

    def test_delete_style(self):
        pass

    def test_create_layer_group(self):
        # Do create
        name = random_string_generator(10)
        layers = (self.test_layer_name,)
        styles = (self.test_style_name,)
        response = self.engine.create_layer_group(layer_group_id=name, layers=layers, styles=styles)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

        # Validate
        result = response['result']
        self.assertEqual(result['name'], name)
        self.assertEqual(result['layers'], layers)
        self.assertEqual(result['styles'], [])

        # Clean up
        self.engine.delete_layer_group(layer_group_id=name)

    def test_create_layer_group_mismatch_layers_styles(self):
        # Do create with differing number of styles and layers
        name = random_string_generator(10)
        layers = (self.test_layer_name,)
        styles = (self.test_style_name, self.test_style_name)
        response = self.engine.create_layer_group(layer_group_id=name, layers=layers, styles=styles)

        # Should fail
        self.assert_valid_response_object(response)
        self.assertFalse(response['success'])

    # @mock.patch('tethys_dataset_services.engines.geoserver_engine.GeoServerCatalog')
    # def test_create_shapefile_resource(self, mock_catalog):
    #     mc = mock_catalog()
    #     mc.create_shapefile_resource.return_value = mock.NonCallableMagicMock(
    #         store=self.store_name,
    #         title='foo',
    #         geometry='points'
    #     )
    #
    #     # Setup
    #     shapefile_name = random_string_generator(15)
    #     shapefile_base = shapefile_name + ".shp"
    #     shapefile_zip = shapefile_name + ".zip"
    #
    #     # Execute
    #     response = self.engine.create_shapefile_resource(store_id=self.store_name,
    #                                                      shapefile_base=shapefile_base,
    #                                                      shapefile_zip=shapefile_zip,
    #                                                      debug=self.debug)
    #
    #     print response

    def test_create_coverage_resource(self):
        raise NotImplementedError()

    def test_create_workspace(self):
        raise NotImplementedError()

    def test_create_style(self):
        raise NotImplementedError()

    def test_create_sql_view(self):
        raise NotImplementedError()
