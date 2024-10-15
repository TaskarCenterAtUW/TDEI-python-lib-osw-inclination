import gc
import json
import pyproj
import networkx as nx
from shapely.geometry import shape, mapping

SCHEMA = 'https://sidewalks.washington.edu/opensidewalks/0.2/schema.json'

class OSMGraph:
    def __init__(self, G=None):
        if G is not None:
            self.G = G

        # Geodesic distance calculator. Assumes WGS84-like geometries.
        self.geod = pyproj.Geod(ellps='WGS84')

    @classmethod
    def from_geojson(cls, nodes_path, edges_path):
        with open(nodes_path) as f:
            nodes_fc = json.load(f)

        with open(edges_path) as f:
            edges_fc = json.load(f)

        G = nx.MultiDiGraph()
        osm_graph = cls(G=G)

        for node_feature in nodes_fc['features']:
            props = node_feature['properties']
            n = props.pop('_id')
            props['geometry'] = shape(node_feature['geometry'])
            G.add_node(n, **props)

        del nodes_fc
        gc.collect()

        for edge_feature in edges_fc['features']:
            props = edge_feature['properties']
            u = props.pop('_u_id')
            v = props.pop('_v_id')
            props['geometry'] = shape(edge_feature['geometry'])
            G.add_edge(u, v, **props)

        del edges_fc
        gc.collect()

        return osm_graph

    def to_geojson(self, *args):
        nodes_path = args[0]
        edges_path = args[1]
        edge_features = []
        for u, v, d in self.G.edges(data=True):
            d_copy = {**d}
            d_copy['_u_id'] = str(u)
            d_copy['_v_id'] = str(v)
            if 'osm_id' in d_copy:
                d_copy.pop('osm_id')
            if 'segment' in d_copy:
                d_copy.pop('segment')

            geometry = mapping(d_copy.pop('geometry'))

            edge_features.append({
                'type': 'Feature',
                'geometry': geometry,
                'properties': d_copy
            })
        edges_fc = {
            'type': 'FeatureCollection',
            'features': edge_features,
            '$schema': SCHEMA
        }

        with open(edges_path, 'w') as f:
            json.dump(edges_fc, f)

        # Delete edge_features and force garbage collection
        del edge_features, edges_fc
        gc.collect()

        node_features = []
        for n, d in self.G.nodes(data=True):
            d_copy = {**d}
            if 'is_point' not in d_copy:
                d_copy['_id'] = str(n)

                if 'osm_id' in d_copy:
                    d_copy.pop('osm_id')

                geometry = mapping(d_copy.pop('geometry'))

                if 'lon' in d_copy:
                    d_copy.pop('lon')

                if 'lat' in d_copy:
                    d_copy.pop('lat')

                node_features.append({
                    'type': 'Feature',
                    'geometry': geometry,
                    'properties': d_copy
                })
        nodes_fc = {
            'type': 'FeatureCollection',
            'features': node_features,
            '$schema': SCHEMA
        }

        with open(nodes_path, 'w') as f:
            json.dump(nodes_fc, f)

        # Delete node_features and force garbage collection
        del node_features, nodes_fc
        gc.collect()

        if len(args) == 3:
            points_path = args[2]
            point_features = []
            for n, d in self.G.nodes(data=True):
                d_copy = {**d}
                if 'is_point' in d_copy:
                    d_copy['_id'] = str(n)

                    if 'osm_id' in d_copy:
                        d_copy.pop('osm_id')

                    geometry = mapping(d_copy.pop('geometry'))

                    d_copy.pop('is_point')

                    if 'lon' in d_copy:
                        d_copy.pop('lon')

                    if 'lat' in d_copy:
                        d_copy.pop('lat')

                    point_features.append({
                        'type': 'Feature',
                        'geometry': geometry,
                        'properties': d_copy
                    })
            points_fc = {
                'type': 'FeatureCollection',
                'features': point_features,
                '$schema': SCHEMA
            }

            with open(points_path, 'w') as f:
                json.dump(points_fc, f)

            # Delete point_features and force garbage collection
            del point_features, points_fc
            gc.collect()

    def clean(self):
        del self.G
        gc.collect()
