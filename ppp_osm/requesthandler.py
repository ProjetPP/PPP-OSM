"""Request handler of the module."""

import pickle
import hashlib
import requests
import memcache
import urllib.parse
from ppp_libmodule import shortcuts
from ppp_libmodule.exceptions import ClientError
from ppp_datamodel.nodes import List, JsonldResource
from ppp_datamodel.nodes import Resource, Triple, Missing, Sentence

from .config import Config

def get_location_as_resource(data):
    # Construct a JSON-LD graph with just the data we want and an identifier
    graph = {'@context': 'http://schema.org',
             '@type': 'GeoCoordinates',
             'latitude': data['lat'],
             'longitude': data['lon'],
             '@reverse': {
                 'geo': {
                    '@type': 'Place',
                    '@id': 'http://www.openstreetmap.org/relation/%s' % data['osm_id'],
                    'name': data['display_name'],
                 }
             }
            }
    # Construct a resource with this graph, and an alternate text for
    # applications that do not support graphs.
    return JsonldResource('%s, %s' % (data['lat'], data['lon']),
            graph=graph)


def connect_memcached():
    mc = memcache.Client(['127.0.0.1'])
    return mc

def _query(url, params):
    return requests.get(url, params=params).json()

def query(url, params):
    """Perform a query to all configured APIs and concatenates all
    results into a single list.
    Also handles caching."""
    mc = connect_memcached()

    # Construct a key suitable for memcached (ie. a string of less than
    # 250 bytes)
    key = (url, params)
    key = 'ppp-osm-%s' + hashlib.md5(pickle.dumps(key)).hexdigest()

    # Get the cached value, if any
    r = mc.get(key)
    if not r:
        # If there is no cached value, query OSM and add the result to
        # the cache.
        r = _query(url, params)
        mc.set(key, r, time=86400)
    return r

def get_locations_as_list(place):
    # Put HTTP escape codes in the place's name
    place = urllib.parse.quote(place)
    # Construct the URL
    url = '%s/%s' % (Config().search_api, place)
    # Make the request and get the content
    d = query(url, {'format': 'json'})
    # Construct a list with all the items
    return List([get_location_as_resource(x) for x in d])
def predicate(node):
    if not isinstance(node, Triple):
        return node
    elif Resource('location') not in node.predicate_set or \
            not isinstance(node.subject, Resource) or \
            not isinstance(node.object, Missing):
        return node
    else:
        # Here, node.subject is a resource, so node.subject.value exists
        # and is a string.
        return get_locations_as_list(node.subject.value)

class RequestHandler:
    def __init__(self, request):
        self.request = request

    def answer(self):
        if isinstance(self.request.tree, Sentence):
            return []
        else:
            tree = self.request.tree.traverse(predicate)
            if tree != self.request.tree:
                # If we have modified the tree, it is relevant to return it
                return [shortcuts.build_answer(self.request, tree, {}, 'OSM')]
            else:
                # Otherwise, we have nothing interesting to say.
                return []
