import unittest
import os
import json
import networkx as nx
from shapely.geometry import Point, LineString
from src.osw_incline.osm_graph import OSMGraph


class TestOSMGraph(unittest.TestCase):

    def setUp(self):
        """Create temporary nodes.geojson and edges.geojson files"""
        self.nodes_geojson = 'nodes.geojson'
        self.edges_geojson = 'edges.geojson'
        self.points_geojson = 'points.geojson'

        # Create a valid nodes.geojson
        nodes_data = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [-122.2342147, 47.4686691]},
                    'properties': {'_id': '298893', 'lon': -122.2342147, 'lat': 47.4686691}
                },
                {
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [-122.235159, 47.4709523]},
                    'properties': {'_id': '298894'}
                }
            ]
        }

        # Create a valid edges.geojson
        edges_data = {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [[-122.2342147, 47.4686691], [-122.2348162, 47.4697331]]
                    },
                    'properties': {
                        '_id': '240256',
                        '_u_id': '298893',
                        '_v_id': '611526',
                        'footway': 'sidewalk',
                        'highway': 'footway',
                        'surface': 'concrete',
                    }
                }
            ]
        }

        # Write the nodes.geojson file
        with open(self.nodes_geojson, 'w') as f:
            json.dump(nodes_data, f)

        # Write the edges.geojson file
        with open(self.edges_geojson, 'w') as f:
            json.dump(edges_data, f)

    def tearDown(self):
        """Remove temporary nodes.geojson and edges.geojson files"""
        if os.path.exists(self.nodes_geojson):
            os.remove(self.nodes_geojson)
        if os.path.exists(self.edges_geojson):
            os.remove(self.edges_geojson)

    def test_from_geojson_nodes(self):
        osm_graph = OSMGraph.from_geojson(self.nodes_geojson, self.edges_geojson)
        self.assertEqual(len(osm_graph.G.nodes), 3)
        self.assertIn('298893', osm_graph.G.nodes)
        self.assertIn('298894', osm_graph.G.nodes)

    def test_from_geojson_edges(self):
        osm_graph = OSMGraph.from_geojson(self.nodes_geojson, self.edges_geojson)
        self.assertEqual(len(osm_graph.G.edges), 1)
        self.assertIn(('298893', '611526'), osm_graph.G.edges)

    def test_to_geojson(self):
        # Create a simple graph with valid Shapely geometry
        G = nx.MultiDiGraph()
        G.add_node('298893', geometry=Point(-122.2342147, 47.4686691))
        G.add_node('298894', geometry=Point(-122.235159, 47.4709523))
        G.add_edge('298893', '298894', geometry=LineString([[-122.2342147, 47.4686691], [-122.235159, 47.4709523]]))

        osm_graph = OSMGraph(G=G)
        osm_graph.to_geojson(self.nodes_geojson, self.edges_geojson)

        # Check if the files exist
        self.assertTrue(os.path.exists(self.nodes_geojson))
        self.assertTrue(os.path.exists(self.edges_geojson))

        # Verify the contents of the nodes.geojson file
        with open(self.nodes_geojson, 'r') as f:
            nodes_data = json.load(f)
            self.assertEqual(len(nodes_data['features']), 2)

        # Verify the contents of the edges.geojson file
        with open(self.edges_geojson, 'r') as f:
            edges_data = json.load(f)
            self.assertEqual(len(edges_data['features']), 1)

    def test_to_geojson_with_osm_id_and_segment(self):
        # Create a graph with 'osm_id' and 'segment' properties in nodes and edges
        G = nx.MultiDiGraph()
        G.add_node('298893', geometry=Point(-122.2342147, 47.4686691), osm_id='123')
        G.add_node('298894', geometry=Point(-122.235159, 47.4709523))
        G.add_edge('298893', '298894', geometry=LineString([[-122.2342147, 47.4686691], [-122.235159, 47.4709523]]),
                   osm_id='456', segment=1)

        osm_graph = OSMGraph(G=G)
        osm_graph.to_geojson(self.nodes_geojson, self.edges_geojson)

        # Check if the files exist
        self.assertTrue(os.path.exists(self.nodes_geojson))
        self.assertTrue(os.path.exists(self.edges_geojson))

        # Verify the contents of the nodes.geojson file
        with open(self.nodes_geojson, 'r') as f:
            nodes_data = json.load(f)
            self.assertEqual(len(nodes_data['features']), 2)
            for feature in nodes_data['features']:
                # Ensure 'osm_id' is removed in the node properties
                self.assertNotIn('osm_id', feature['properties'])

        # Verify the contents of the edges.geojson file
        with open(self.edges_geojson, 'r') as f:
            edges_data = json.load(f)
            self.assertEqual(len(edges_data['features']), 1)
            for feature in edges_data['features']:
                # Ensure 'osm_id' and 'segment' are removed in the edge properties
                self.assertNotIn('osm_id', feature['properties'])
                self.assertNotIn('segment', feature['properties'])

    def test_to_geojson_with_lon_lat(self):
        # Create a graph with 'lon' and 'lat' properties in nodes
        G = nx.MultiDiGraph()
        G.add_node('298893', geometry=Point(-122.2342147, 47.4686691), lon=-122.2342147, lat=47.4686691)
        G.add_node('298894', geometry=Point(-122.235159, 47.4709523))
        G.add_edge('298893', '298894', geometry=LineString([[-122.2342147, 47.4686691], [-122.235159, 47.4709523]]))

        osm_graph = OSMGraph(G=G)
        osm_graph.to_geojson(self.nodes_geojson, self.edges_geojson)

        # Check if the files exist
        self.assertTrue(os.path.exists(self.nodes_geojson))
        self.assertTrue(os.path.exists(self.edges_geojson))

        # Verify the contents of the nodes.geojson file
        with open(self.nodes_geojson, 'r') as f:
            nodes_data = json.load(f)
            self.assertEqual(len(nodes_data['features']), 2)

            # Verify that 'lon' and 'lat' were removed from the node properties
            for feature in nodes_data['features']:
                self.assertNotIn('lon', feature['properties'])
                self.assertNotIn('lat', feature['properties'])

        # Verify the contents of the edges.geojson file
        with open(self.edges_geojson, 'r') as f:
            edges_data = json.load(f)
            self.assertEqual(len(edges_data['features']), 1)

    def test_to_geojson_with_points(self):
        # Create a graph with 'is_point', 'lon', and 'lat' properties in nodes
        G = nx.MultiDiGraph()
        G.add_node('298893', geometry=Point(-122.2342147, 47.4686691), is_point=True, lon=-122.2342147, lat=47.4686691)
        G.add_node('298894', geometry=Point(-122.235159, 47.4709523), is_point=True, lon=-122.235159, lat=47.4709523)
        G.add_edge('298893', '298894', geometry=LineString([[-122.2342147, 47.4686691], [-122.235159, 47.4709523]]))

        osm_graph = OSMGraph(G=G)
        osm_graph.to_geojson(self.nodes_geojson, self.edges_geojson, self.points_geojson)

        # Check if the files exist
        self.assertTrue(os.path.exists(self.nodes_geojson))
        self.assertTrue(os.path.exists(self.edges_geojson))
        self.assertTrue(os.path.exists(self.points_geojson))

        # Verify the contents of the nodes.geojson file
        with open(self.nodes_geojson, 'r') as f:
            nodes_data = json.load(f)
            self.assertEqual(len(nodes_data['features']), 0)  # Expect no regular nodes since they are all points

        # Verify the contents of the points.geojson file
        with open(self.points_geojson, 'r') as f:
            points_data = json.load(f)
            self.assertEqual(len(points_data['features']), 2)

            # Verify that 'is_point', 'lon', and 'lat' were removed from the point properties
            for feature in points_data['features']:
                self.assertNotIn('lon', feature['properties'])
                self.assertNotIn('lat', feature['properties'])
                self.assertNotIn('is_point', feature['properties'])

    def test_to_geojson_with_osm_id_removal(self):
        # Create a graph with 'osm_id' property in nodes and edges
        G = nx.MultiDiGraph()
        G.add_node('298893', geometry=Point(-122.2342147, 47.4686691), osm_id='node_osm_id')
        G.add_node('298894', geometry=Point(-122.235159, 47.4709523))
        G.add_edge('298893', '298894', geometry=LineString([[-122.2342147, 47.4686691], [-122.235159, 47.4709523]]),
                   osm_id='edge_osm_id')

        osm_graph = OSMGraph(G=G)
        osm_graph.to_geojson(self.nodes_geojson, self.edges_geojson)

        # Check if the files exist
        self.assertTrue(os.path.exists(self.nodes_geojson))
        self.assertTrue(os.path.exists(self.edges_geojson))

        # Verify the contents of the nodes.geojson file
        with open(self.nodes_geojson, 'r') as f:
            nodes_data = json.load(f)
            self.assertEqual(len(nodes_data['features']), 2)
            for feature in nodes_data['features']:
                # Ensure 'osm_id' is removed in the node properties
                self.assertNotIn('osm_id', feature['properties'])

        # Verify the contents of the edges.geojson file
        with open(self.edges_geojson, 'r') as f:
            edges_data = json.load(f)
            self.assertEqual(len(edges_data['features']), 1)
            for feature in edges_data['features']:
                # Ensure 'osm_id' is removed in the edge properties
                self.assertNotIn('osm_id', feature['properties'])

    def test_to_geojson_with_points_and_osm_id(self):
        # Create a graph with 'is_point' and 'osm_id' properties in nodes
        G = nx.MultiDiGraph()
        G.add_node('298893', geometry=Point(-122.2342147, 47.4686691), is_point=True, osm_id='point_osm_id',
                   lon=-122.2342147, lat=47.4686691)
        G.add_node('298894', geometry=Point(-122.235159, 47.4709523), is_point=True, lon=-122.235159, lat=47.4709523)
        G.add_edge('298893', '298894', geometry=LineString([[-122.2342147, 47.4686691], [-122.235159, 47.4709523]]))

        osm_graph = OSMGraph(G=G)
        osm_graph.to_geojson(self.nodes_geojson, self.edges_geojson, self.points_geojson)

        # Check if the files exist
        self.assertTrue(os.path.exists(self.nodes_geojson))
        self.assertTrue(os.path.exists(self.edges_geojson))
        self.assertTrue(os.path.exists(self.points_geojson))

        # Verify the contents of the points.geojson file
        with open(self.points_geojson, 'r') as f:
            points_data = json.load(f)
            self.assertEqual(len(points_data['features']), 2)

            for feature in points_data['features']:
                # Ensure 'osm_id' is removed in the point properties
                self.assertNotIn('osm_id', feature['properties'])

        # Verify that the nodes.geojson still has no points (test separation of files)
        with open(self.nodes_geojson, 'r') as f:
            nodes_data = json.load(f)
            self.assertEqual(len(nodes_data['features']), 0)

    def test_clean(self):
        osm_graph = OSMGraph.from_geojson(self.nodes_geojson, self.edges_geojson)
        self.assertEqual(len(osm_graph.G.nodes), 3)
        osm_graph.clean()
        self.assertFalse(hasattr(osm_graph, 'G'))


if __name__ == '__main__':
    unittest.main()
