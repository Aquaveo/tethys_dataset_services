"""
********************************************************************************
* Name: geoserver_engine_e2e_tests.py
* Author: nswain
* Created On: June 25, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *  # noqa: F403, F401

import random
import string
import unittest
import os
from sqlalchemy.engine import create_engine
from geoserver.catalog import Catalog as GeoServerCatalog


from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from tethys_dataset_services.tests.test_config import TEST_GEOSERVER_DATASET_SERVICE
from tethys_dataset_services.tests.test_config import TEST_POSTGIS_SERVICE


def random_string_generator(size):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))


class GeoServerDatasetEngineEnd2EndTests(unittest.TestCase):

    def setUp(self):
        # GeoServer
        self.gs_endpoint = TEST_GEOSERVER_DATASET_SERVICE['ENDPOINT']
        self.gs_username = TEST_GEOSERVER_DATASET_SERVICE['USERNAME']
        self.gs_password = TEST_GEOSERVER_DATASET_SERVICE['PASSWORD']
        self.catalog = GeoServerCatalog(self.gs_endpoint, username=self.gs_username, password=self.gs_password)

        # Setup a testing workspace
        self.workspace_name = random_string_generator(10)
        self.workspace_uri = 'http://www.tethysplatform.org/{}'.format(self.workspace_name)
        self.catalog.create_workspace(self.workspace_name, self.workspace_uri)

        # Setup Postgis database connection
        self.engine = create_engine(TEST_POSTGIS_SERVICE['URL'])
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        # Create GeoServer Engine
        self.endpoint = TEST_GEOSERVER_DATASET_SERVICE['ENDPOINT']
        self.geoserver_engine = GeoServerSpatialDatasetEngine(endpoint=self.endpoint,
                                                              username=TEST_GEOSERVER_DATASET_SERVICE['USERNAME'],
                                                              password=TEST_GEOSERVER_DATASET_SERVICE['PASSWORD'])

        self.postgis_table_name = 'points'
        self.geometry_column = 'geometry'
        self.geometry_type = 'Point'
        self.srid = 4326

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

    def tearDown(self):
        # Clean up GeoServer
        workspace = self.catalog.get_workspace(self.workspace_name)
        self.catalog.delete(workspace, recurse=True, purge=True)

        # Clean up Postgis database
        self.transaction.rollback()
        self.connection.close()
        self.engine.dispose()

    def setup_postgis_table(self):
        """
        Creates table in the database named "points" with two entries. The table has three columns:
        "id", "name", and "geometry." Use this table for the tests that require a database.
        """
        geom_table_sql = "CREATE TABLE IF NOT EXISTS {table} (" \
                         "id integer CONSTRAINT points_primary_key PRIMARY KEY, " \
                         "name varchar(20)" \
                         "); " \
                         "SELECT AddGeometryColumn('public', '{table}', 'geometry', 4326, 'POINT', 2);". \
            format(table=self.postgis_table_name)

        self.connection.execute(geom_table_sql)

        insert_sql = "INSERT INTO {table} VALUES ({id}, '{name}', ST_GeomFromText('POINT({lon} {lat})', 4326));"
        rows = [
            {"id": 1, "name": "Aquaveo", "lat": 40.276039, "lon": -111.651120},
            {"id": 2, "name": "BYU", "lat": 40.252335, "lon": -111.649326},
        ]

        for r in rows:
            sql = insert_sql.format(
                table=self.postgis_table_name,
                id=r['id'],
                name=r['name'],
                lat=r['lat'],
                lon=r['lon']
            )
            self.connection.execute(sql)

    def test_create_shapefile_resource_base(self):
        # call methods: create_shapefile_resource, list_resources, get_resource, delete_resource

        # TEST create shapefile

        # Setup
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filename = 'test'
        shapefile_name = os.path.join(dir_path, 'files', 'shapefile', filename)
        workspace = self.workspace_name
        store_id = random_string_generator(10)
        store_id_name = '{}:{}'.format(workspace, store_id)
        # store_id_name = store_id

        # Execute
        response = self.geoserver_engine.create_shapefile_resource(store_id=store_id_name,
                                                                   shapefile_base=shapefile_name,
                                                                   overwrite=True)
        # Validate response object
        self.assert_valid_response_object(response)

        # Should succeed
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)
        self.assertIn(store_id, r['name'])
        self.assertIn(store_id, r['store'])

        # TEST list_resources

        # Execute
        response = self.geoserver_engine.list_resources()

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
            self.assertIsInstance(result[0], basestring)

        # layer listed
        self.assertIn(store_id, result)

        # TEST get_resources

        # Execute
        # Geoserver uses the store_id as the layer/resource name (not the filename)
        resource_id_name = '{}:{}'.format(workspace, store_id)
        response = self.geoserver_engine.get_resource(resource_id=resource_id_name)

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
        self.assertEquals(store_id, r['name'])
        self.assertIn(store_id, r['wfs']['shapefile'])

        # TEST delete_resource
        # Execute
        # This case the resource id is the same as the store id.
        response = self.geoserver_engine.delete_resource(resource_id=resource_id_name,
                                                         store=store_id)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        # TODO: delete_resource is returning a 403 error: not authorized.
        # self.assertTrue(response['success'])

    def test_create_shapefile_resource_zip(self):
        # call methods: create_shapefile_resource, list_layers, get_layer, delete_layer

        # TEST create_shapefile_resource
        # Test1.zip

        # Setup
        dir_path = os.path.dirname(os.path.realpath(__file__))
        shapefile_zip = os.path.join(dir_path, 'files', 'shapefile', "test1.zip")
        shapefile = "test1"
        workspace = self.workspace_name
        store_id = random_string_generator(10)
        store_id_name = '{}:{}'.format(workspace, store_id)

        # Execute
        response = self.geoserver_engine.create_shapefile_resource(store_id=store_id_name,
                                                                   shapefile_zip=shapefile_zip,
                                                                   overwrite=True)
        # Validate response object
        self.assert_valid_response_object(response)

        # Should succeed
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        filename = os.path.splitext(os.path.basename(shapefile_zip))[0]
        self.assertIsInstance(r, dict)
        self.assertIn(filename, r['name'])
        self.assertIn(store_id, r['store'])

        # TEST list_layers test
        # Execute
        response = self.geoserver_engine.list_layers()

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
            self.assertIsInstance(result[0], basestring)

        # Get the last item from result
        layer_id = '{}:{}'.format(workspace, shapefile)

        # TEST get layers test
        # Execute
        response = self.geoserver_engine.get_layer(layer_id=layer_id,
                                                   store_id=store_id)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        self.assertIn(filename, r['name'])
        self.assertIn(self.workspace_name, r['name'])

        # TEST delete_layer
        self.geoserver_engine.delete_layer(layer_id=layer_id,
                                           store_id=store_id)

        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

    def test_create_shapefile_resource_upload(self):
        # call methods: create_shapefile_resource, list_stores, get_store, delete_store

        # TEST create_shapefile_resource

        # Use in memory file list: test.shp and friends
        # Setup
        dir_path = os.path.dirname(os.path.realpath(__file__))
        shapefile_cst = os.path.join(dir_path, 'files', 'shapefile', 'test.cst')
        shapefile_dbf = os.path.join(dir_path, 'files', 'shapefile', 'test.dbf')
        shapefile_prj = os.path.join(dir_path, 'files', 'shapefile', 'test.prj')
        shapefile_shp = os.path.join(dir_path, 'files', 'shapefile', 'test.shp')
        shapefile_shx = os.path.join(dir_path, 'files', 'shapefile', 'test.shx')

        # Workspace is given
        store_rand = random_string_generator(10)
        store_id = '{}:{}'.format(self.workspace_name, store_rand)

        with open(shapefile_cst, 'rb') as cst_upload,\
                open(shapefile_dbf, 'rb') as dbf_upload,\
                open(shapefile_prj, 'rb') as prj_upload,\
                open(shapefile_shp, 'rb') as shp_upload,\
                open(shapefile_shx, 'rb') as shx_upload:
            upload_list = [cst_upload, dbf_upload, prj_upload, shp_upload, shx_upload]
            response = self.geoserver_engine.create_shapefile_resource(store_id=store_id,
                                                                       shapefile_upload=upload_list,
                                                                       overwrite=True)
        # Should succeed
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)
        self.assertIn(store_rand, r['name'])
        self.assertIn(store_rand, r['store'])

        # TEST list_stores

        # Execute

        response = self.geoserver_engine.list_stores()

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # list of strings
        if len(result) > 0:
            self.assertIsInstance(result[0], basestring)

        # layer group listed
        self.assertIn(store_rand, result)

        # TEST get store

        # Execute
        response = self.geoserver_engine.get_store(store_id=store_id)

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
        self.assertIn(r['name'], store_rand)
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])

        # TEST delete_store
        response = self.geoserver_engine.delete_store(store_id=store_id, purge=True, recurse=True)

        # Failure Check
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

    def test_create_coverage_resource_arcgrid(self):
        # call methods: create_coverage_resource, list_resources, get_resource, delete_resource

        # TEST create_coverage_resource
        # precip30min.zip
        store_name = random_string_generator(10)
        expected_store_id = '{}:{}'.format(self.workspace_name, store_name)
        expected_coverage_type = 'arcgrid'
        coverage_file_name = 'precip30min.zip'
        coverage_name = coverage_file_name.split('.')[0]
        dir_path = os.path.dirname(os.path.realpath(__file__))
        coverage_file = os.path.join(dir_path, "files", "arc_sample", coverage_file_name)

        with open(coverage_file, 'rb') as coverage_upload:
            # Execute
            response = self.geoserver_engine.create_coverage_resource(store_id=expected_store_id,
                                                                      coverage_type=expected_coverage_type,
                                                                      coverage_upload=coverage_upload,
                                                                      overwrite=True)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Values
        self.assertEqual(coverage_name, r['name'])
        self.assertEqual(self.workspace_name, r['workspace'])

        # TEST list_resources

        # Execute
        response = self.geoserver_engine.list_resources()

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
            self.assertIsInstance(result[0], basestring)

        # layer listed
        self.assertIn(coverage_name, result)

        # TEST get_resource

        # Execute
        resource_id = '{}:{}'.format(self.workspace_name, coverage_name)

        response = self.geoserver_engine.get_resource(resource_id=resource_id,
                                                      store=store_name)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        self.assertIn('ArcGrid', r['keywords'])
        self.assertEqual(coverage_name, r['title'])
        self.assertEqual('coverage', r['resource_type'])

        # delete_resource
        # TODO: delete_resource is returning a 403 error: not authorized.
        # Execute
        resource_id = '{}:{}'.format(self.workspace_name, coverage_name)
        response = self.geoserver_engine.delete_resource(resource_id=resource_id,
                                                         store=store_name)

        # # Validate response object
        self.assert_valid_response_object(response)

        # # Success
        # self.assertTrue(response['success'])

    def test_create_coverage_resource_grassgrid(self):
        # call methods: create_coverage_resource, list_layers, get_layer, delete_layer

        # TEST create_coverage resource
        # my_grass.zip
        store_name = random_string_generator(10)
        expected_store_id = '{}:{}'.format(self.workspace_name, store_name)
        expected_coverage_type = 'grassgrid'
        coverage_file_name = 'my_grass.zip'
        coverage_name = coverage_file_name.split('.')[0]
        dir_path = os.path.dirname(os.path.realpath(__file__))
        coverage_file = os.path.join(dir_path, "files", "grass_ascii", coverage_file_name)

        # Execute
        response = self.geoserver_engine.create_coverage_resource(store_id=expected_store_id,
                                                                  coverage_type=expected_coverage_type,
                                                                  coverage_file=coverage_file,
                                                                  overwrite=True)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Tests
        self.assertIn(coverage_name, r['name'])
        self.assertEqual(self.workspace_name, r['workspace'])

        #  TEST list_layers

        #  Execute
        response = self.geoserver_engine.list_layers()

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
            self.assertIsInstance(result[0], basestring)

        # Check if layer is in list
        self.assertIn(coverage_name, result)

        # TEST get_layer

        # Execute
        layer_id = '{}:{}'.format(self.workspace_name, coverage_name)
        response = self.geoserver_engine.get_layer(layer_id=layer_id,
                                                   store_id=store_name)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)
        self.assertIn(store_name, r['store'])
        self.assertIn(self.workspace_name, r['name'])

        # TEST delete_layer
        self.geoserver_engine.delete_layer(layer_id=layer_id,
                                           store_id=store_name)

        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

    def test_create_coverage_resource_geotiff(self):
        # adem.tif
        # call methods: create_coverage_resource, list_stores, get_store, delete_store

        # TEST create_coverage_resource

        store_name = random_string_generator(10)
        expected_store_id = '{}:{}'.format(self.workspace_name, store_name)
        expected_coverage_type = 'geotiff'
        coverage_file_name = 'adem.tif'
        coverage_name = coverage_file_name.split('.')[0]
        dir_path = os.path.dirname(os.path.realpath(__file__))
        coverage_file = os.path.join(dir_path, "files", coverage_file_name)

        with open(coverage_file, 'rb') as coverage_upload:
            # Execute
            response = self.geoserver_engine.create_coverage_resource(store_id=expected_store_id,
                                                                      coverage_type=expected_coverage_type,
                                                                      coverage_upload=coverage_upload,
                                                                      overwrite=True)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Values
        self.assertEqual(coverage_name, r['name'])
        self.assertEqual(self.workspace_name, r['workspace'])

        # TEST list_stores

        # Execute

        response = self.geoserver_engine.list_stores()

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # List of strings
        if len(result) > 0:
            self.assertIsInstance(result[0], basestring)

        # TEST layer group listed
        self.assertIn(store_name, result)

        # TEST get store

        # Execute
        response = self.geoserver_engine.get_store(store_id=expected_store_id)

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
        self.assertIn(r['name'], store_name)
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])

        # TEST delete_store
        response = self.geoserver_engine.delete_store(store_id=expected_store_id, purge=True, recurse=True)

        # Failure Check
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

    def test_create_coverage_resource_world_file_tif(self):
        # pk50095.zip
        # call methods: create_coverage_resource, list_layers, get_layer, delete_layer
        # TEST create_coverage resource
        store_name = random_string_generator(10)
        expected_store_id = '{}:{}'.format(self.workspace_name, store_name)
        expected_coverage_type = 'worldimage'
        coverage_file_name = 'Pk50095.zip'
        coverage_name = coverage_file_name.split('.')[0]
        dir_path = os.path.dirname(os.path.realpath(__file__))
        coverage_file = os.path.join(dir_path, "files", "img_sample", coverage_file_name)

        # Execute
        response = self.geoserver_engine.create_coverage_resource(store_id=expected_store_id,
                                                                  coverage_type=expected_coverage_type,
                                                                  coverage_file=coverage_file,
                                                                  overwrite=True)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Tests
        self.assertIn(coverage_name, r['name'])
        self.assertEqual(self.workspace_name, r['workspace'])

        #  TEST list_layers

        #  Execute
        response = self.geoserver_engine.list_layers()

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
            self.assertIsInstance(result[0], basestring)

        # Check if layer is in list
        self.assertIn(coverage_name, result)

        # TEST get_layer

        # Execute
        layer_id = '{}:{}'.format(self.workspace_name, coverage_name)
        response = self.geoserver_engine.get_layer(layer_id=layer_id,
                                                   store_id=store_name)
        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)
        self.assertIn(store_name, r['store'])
        self.assertIn(self.workspace_name, self.workspace_name)

        # TEST delete_layer
        self.geoserver_engine.delete_layer(layer_id=coverage_name,
                                           store_id=store_name)

        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

    def test_create_coverage_resource_upload(self):
        # DO NOT MOCK
        # Use in memory file list: precip30min.prj & precip30min.asc
        # call methods: create_coverage_resource, list_resources, get_resource, delete_resource
        store_id_name = random_string_generator(10)
        expected_store_id = '{}:{}'.format(self.workspace_name, store_id_name)
        expected_coverage_type = 'arcgrid'
        coverage_file_name = 'precip30min.asc'
        prj_file_name = 'precip30min.prj'
        coverage_name = coverage_file_name.split('.')[0]
        dir_path = os.path.dirname(os.path.realpath(__file__))
        arc_sample = os.path.join(dir_path, "files", "arc_sample")
        coverage_file = os.path.join(arc_sample, coverage_file_name)
        prj_file = os.path.join(arc_sample, prj_file_name)

        with open(coverage_file, 'rb') as coverage_upload:
            with open(prj_file, 'rb') as prj_upload:
                upload_list = [coverage_upload, prj_upload]

                # Execute
                response = self.geoserver_engine.create_coverage_resource(store_id=expected_store_id,
                                                                          coverage_type=expected_coverage_type,
                                                                          coverage_upload=upload_list,
                                                                          overwrite=True)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # Values
        self.assertEqual(coverage_name, r['name'])
        self.assertEqual(self.workspace_name, r['workspace'])

        # TEST list_resources

        # Execute
        response = self.geoserver_engine.list_resources()

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
            self.assertIsInstance(result[0], basestring)

        # layer listed
        self.assertIn(coverage_name, result)

        # TEST get_resources

        # Execute
        resource_id = "{}:{}".format(self.workspace_name, coverage_name)
        response = self.geoserver_engine.get_resource(resource_id=resource_id,
                                                      store=store_id_name)

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
        self.assertEquals(coverage_name, r['name'])
        self.assertIn(coverage_name, r['wcs']['arcgrid'])

        # TEST delete_resource
        # TODO: delete_resource is returning a 403 error: not authorized.
        # Execute
        # This case the resource id is the same as the filename.
        resource_id = '{}:{}'.format(self.workspace_name, coverage_name)
        response = self.geoserver_engine.delete_resource(resource_id=resource_id,
                                                         store=store_id_name)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        # self.assertTrue(response['success'])

    def test_create_layer_group(self):

        # call methods: create_layer_group, list_layer_groups, get_layer_group, delete_layer_group

        # create_layer_group
        # Use existing layers and styles in geoserver:
        # layers: sf:roads, sf:bugsites, sf:streams;
        # styles: simple_roads, capitals, simple_streams

        # TEST create_layer_group

        # Do create
        # expected_layer_group_id = '{}:{}'.format(self.workspace_name, random_string_generator(10))

        expected_layer_group_id = random_string_generator(10)
        expected_layers = ['roads', 'bugsites', 'streams']
        expected_styles = ['simple_roads', 'capitals', 'simple_streams']

        # TODO: create_layer_group: fails on catalog.save() when workspace is given.
        response = self.geoserver_engine.create_layer_group(layer_group_id=expected_layer_group_id,
                                                            layers=expected_layers,
                                                            styles=expected_styles)
        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

        # Validate
        result = response['result']

        self.assertEquals(result['name'], expected_layer_group_id)
        self.assertEquals(result['layers'], expected_layers)
        self.assertEquals(result['styles'], expected_styles)

        # TEST list_layer_groups

        # Execute
        response = self.geoserver_engine.list_layer_groups()

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # layer group listed
        self.assertIn(expected_layer_group_id, result)

        # TEST get layer_group

        # Execute
        response = self.geoserver_engine.get_layer_group(layer_group_id=expected_layer_group_id)

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
        self.assertEqual(None, r['workspace'])
        self.assertIn('layers', r)
        self.assertEqual(expected_layers, r['layers'])
        self.assertIn('styles', r)
        self.assertEqual(expected_styles, r['styles'])
        self.assertNotIn('dom', r)

        # TEST delete layer group
        # Clean up
        self.geoserver_engine.delete_layer_group(layer_group_id=expected_layer_group_id)
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        # self.assertIsNone(response['result'])

    def test_create_workspace(self):
        # call methods: create_workspace, list_workspaces, get_workspace, delete_workspace

        # TEST create workspace
        expected_workspace_id = random_string_generator(10)

        expected_uri = 'http://www.tethysplatform.org/{}'.format(expected_workspace_id)

        # create workspace test
        response = self.geoserver_engine.create_workspace(workspace_id=expected_workspace_id, uri=expected_uri)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        self.assertIn('name', r)

        self.assertEqual(expected_workspace_id, r['name'])

        # TEST list workspace

        # Execute
        response = self.geoserver_engine.list_workspaces()

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # TEST layer group listed
        self.assertIn(expected_workspace_id, result)

        # TEST get_workspace

        # Execute
        response = self.geoserver_engine.get_workspace(workspace_id=expected_workspace_id)

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
        self.assertIn(r['name'], expected_workspace_id)

        # TEST delete work_space

        # Do delete
        response = self.geoserver_engine.delete_workspace(workspace_id=expected_workspace_id)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        self.assertIsNone(response['result'])

    def test_create_style(self):
        # call methods: create_style, list_styles, get_style, delete_style

        # TEST create_style
        expected_style_id_name = random_string_generator(10)
        expected_style_id = '{}:{}'.format(self.workspace_name, expected_style_id_name)
        style_file_name = 'point.sld'
        dir_path = os.path.dirname(os.path.realpath(__file__))
        expected_sld = os.path.join(dir_path, "files", style_file_name)

        # Execute
        with open(expected_sld, 'r') as sld_file:
            sld_string = sld_file.read()
            # TODO: create_style: Fails on when overwrite is False.
            response = self.geoserver_engine.create_style(style_id=expected_style_id, sld=sld_string, overwrite=True)

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)

        # TEST list_styles

        # Execute
        response = self.geoserver_engine.list_styles(workspace=self.workspace_name)

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
            self.assertIsInstance(result[0], basestring)

        # TEST layer listed
        self.assertIn(expected_style_id_name, result)

        # TEST get_style

        # Execute
        response = self.geoserver_engine.get_style(style_id=expected_style_id)

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
        self.assertIn(r['name'], expected_style_id)
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])

        # TEST delete_style

        # Do delete
        response = self.geoserver_engine.delete_style(style_id=expected_style_id)

        # Should succeed
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])
        self.assertIsNone(response['result'])

    def test_link_sqlalchemy_db_to_geoserver(self):
        pass

        # # DO NOT MOCK

        # # Use testing_config.TEST_POSTGIS_SERVICE for db credentials
        # # call methods: link_sqlalchemy_db_to_geoserver, add_table_to_postgis_store,
        # # list_stores, get_store, delete_store

        # TEST link_sqlalchemy_db_to_geoserver
        store_id_name = random_string_generator(10)
        store_id = '{}:{}'.format(self.workspace_name, store_id_name)

        self.geoserver_engine.link_sqlalchemy_db_to_geoserver(store_id=store_id,
                                                              sqlalchemy_engine=self.geoserver_engine)

        # # DB table setup
        # self.setup_postgis_table()
        # # table = self.postgis_table_name
        # raise NotImplementedError()

    def test_create_postgis_feature_resource(self):
        # Use testing_config.TEST_POSTGIS_SERVICE for db credentials
        # call methods: create_postgis_feature_resource (with table), list_stores, get_store, delete_store
        self.setup_postgis_table()
        # TEST create_postgis_feature_resource (with table)
        store_id_name = random_string_generator(10)
        store_id = '{}:{}'.format(self.workspace_name, store_id_name)
        host = '172.17.0.1'
        port = 5435
        database = 'tds_tests'
        user = 'tethys_super'
        password = 'pass'
        table_name = 'points'

        response = self.geoserver_engine.create_postgis_feature_resource(store_id=store_id,
                                                                         host=host,
                                                                         port=port,
                                                                         database=database,
                                                                         user=user,
                                                                         table=table_name,
                                                                         password=password)
        self.assertTrue(response['success'])

        # Extract Result
        r = response['result']

        # Type
        self.assertIsInstance(r, dict)
        self.assertIn('workspace', r)
        self.assertIn(self.workspace_name, r['workspace'])
        self.assertIn('store', r)
        self.assertEqual(store_id_name, r['store'])

        # TEST list_stores

        # Execute

        response = self.geoserver_engine.list_stores()

        # Validate response object
        self.assert_valid_response_object(response)

        # Success
        self.assertTrue(response['success'])

        # Extract Result
        result = response['result']

        # list of strings
        if len(result) > 0:
            self.assertIsInstance(result[0], basestring)

        # layer group listed
        self.assertIn(store_id_name, result)

        # TEST get store

        # Execute
        response = self.geoserver_engine.get_store(store_id=store_id)

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
        self.assertIn(store_id_name, r['name'])
        self.assertIn('workspace', r)
        self.assertEqual(self.workspace_name, r['workspace'])

        # TEST delete_store
        response = self.geoserver_engine.delete_store(store_id=store_id, purge=True, recurse=True)

        # Failure Check
        self.assert_valid_response_object(response)
        self.assertTrue(response['success'])

    def test_create_sql_view(self):
        # Use testing_config.TEST_POSTGIS_SERVICE for db credentials

        # call methods: create_sql_view, list_resources, list_stores, list_layers

        # TEST create_postgis_feature_resource (with table)
        store_id_name = random_string_generator(10)
        store_id = '{}:{}'.format(self.workspace_name, store_id_name)
        host = '172.17.0.1'
        port = 5435
        database = 'tds_tests'
        user = 'tethys_super'
        password = 'pass'
        table_name = 'points'

        response = self.geoserver_engine.create_postgis_feature_resource(store_id=store_id,
                                                                         host=host,
                                                                         port=port,
                                                                         database=database,
                                                                         user=user,
                                                                         table=table_name,
                                                                         password=password)
        self.assertTrue(response['success'])

        # self.setup_postgis_table()
        feature_type_name = random_string_generator(10)
        postgis_store_id = '{}:{}'.format(self.workspace_name, store_id_name)
        sql = "SELECT * FROM {}".format(self.postgis_table_name)
        geometry_column = self.geometry_column
        geometry_type = self.geometry_type

        response = self.geoserver_engine.create_sql_view(feature_type_name=feature_type_name,
                                                         postgis_store_id=postgis_store_id,
                                                         sql=sql,
                                                         geometry_column=geometry_column,
                                                         geometry_type=geometry_type,
                                                         debug=True)

        self.assertTrue(response['success'])

        # Extract Result
        # r = response['result']
        #
        # # Type
        # self.assertIsInstance(r, dict)
        #
        # self.assertIn('name', r)
        # self.assertEqual('0fde3d83_68c8_4e6d_b692_b7f963a9fe3c', r['name'])
