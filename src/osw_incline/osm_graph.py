import gc
import json
import pyproj
import networkx as nx
from shapely.geometry import shape, mapping


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

        for edge_feature in edges_fc['features']:
            props = edge_feature['properties']
            u = props.pop('_u_id')
            v = props.pop('_v_id')
            props['geometry'] = shape(edge_feature['geometry'])
            G.add_edge(u, v, **props)

        del nodes_fc
        del edges_fc
        gc.collect()

        return osm_graph

    def to_geojson(self, *args):
        nodes_path = args[0]
        edges_path = args[1]

        # Load the original files to retain the original top-level keys
        with open(nodes_path) as f:
            original_nodes_fc = json.load(f)

        with open(edges_path) as f:
            original_edges_fc = json.load(f)

        # Process the edges
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

        # Update the original edges feature collection
        original_edges_fc['features'] = edge_features

        # Process the nodes
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

        # Update the original nodes feature collection
        original_nodes_fc['features'] = node_features

        # Write the updated nodes and edges to the files
        with open(edges_path, 'w') as f:
            json.dump(original_edges_fc, f)

        with open(nodes_path, 'w') as f:
            json.dump(original_nodes_fc, f)

        # Handle points if the third argument (points_path) is provided
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

            with open(points_path, 'w') as f:
                json.dump({'type': 'FeatureCollection', 'features': point_features}, f)

        del original_nodes_fc
        del original_edges_fc
        gc.collect()
