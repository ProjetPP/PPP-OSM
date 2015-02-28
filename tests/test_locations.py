from ppp_datamodel import Missing, Triple, Resource, List
from ppp_datamodel.communication import Request, TraceItem, Response
from ppp_libmodule.tests import PPPTestCase
from ppp_osm import app

class TestLocation(PPPTestCase(app)):
    config_var = 'PPP_OSM_CONFIG'
    config = '{"search_api": "http://nominatim.openstreetmap.org/search"}'
    def testNoError(self):
        # Prepare the request
        q = Request('1', 'en', Triple(Resource('Jouy aux Arches'), Resource('location'), Missing()), {}, [])
        # Make sure it returns a 200 HTTP code.
        self.assertStatusInt(q, 200)

    def testBasics(self):
        # Prepare the request
        q = Request('1', 'en', Triple(Resource('Jouy aux Arches'), Resource('location'), Missing()), {}, [])
        # Send the request and receive a response
        r = self.request(q)

        # Usual stuff
        self.assertEqual(len(r), 1, r)
        self.assertIsInstance(r[0].tree, List)
        self.assertGreater(len(r[0].tree.list), 0, r[0].tree)
        self.assertEqual('49.0616, 6.0784', r[0].tree.list[0].value)
        self.assertIn('Jouy-aux-Arches',
                r[0].tree.list[0].graph['@reverse']['geo']['name'])
