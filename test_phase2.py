"""
Phase 2 Validation Test Suite
------------------------------
Tests:
1. Bugfix: /about and /contact templates exist and render with 200 OK.
2. M2.1: 0-100 Composite Safety Score & Domain Sub-Scores.
3. M2.2: /api/map-data for Leaflet Geographic Map.
4. M2.4: /compare Route & comparison engine (Mumbai vs Pune).
5. S2.2: ARIMA Confidence Interval bands.
"""

import unittest
import json
from app import app
from crime_analysis import CrimeAnalyzer
from crime_prediction import CrimePredictor

class Phase2ValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.analyzer = CrimeAnalyzer('crime_data_clean.csv')
        cls.predictor = CrimePredictor('crime_data_clean.csv')

    def test_01_about_page_template_found(self):
        """Verify /about renders without TemplateNotFound error."""
        res = self.client.get('/about')
        self.assertEqual(res.status_code, 200, "GET /about failed!")
        html = res.data.decode('utf-8')
        self.assertIn("About", html)
        self.assertIn("National Crime Records Bureau", html)
        print("\n[PASS] GET /about returned 200 OK without TemplateNotFound")

    def test_02_contact_page_template_found(self):
        """Verify /contact renders without TemplateNotFound error and handles POST."""
        res = self.client.get('/contact')
        self.assertEqual(res.status_code, 200, "GET /contact failed!")
        html = res.data.decode('utf-8')
        self.assertIn("Send us a Message", html)
        self.assertIn("112", html)

        # Test POST
        res_post = self.client.post('/contact', data={
            'name': 'Adeen',
            'email': 'adeen@example.com',
            'message': 'Testing contact form'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn("Your message has been received", res_post.data.decode('utf-8'))
        print("[PASS] GET & POST /contact returned 200 OK with flash confirmation")

    def test_03_safety_score_calculation(self):
        """M2.1: Verify 0-100 Safety Score and Domain Sub-Scores."""
        analysis = self.analyzer.generate_crime_analysis('MUMBAI')
        self.assertIsNotNone(analysis)
        self.assertIn('safety_score', analysis)
        self.assertGreaterEqual(analysis['safety_score'], 0)
        self.assertLessEqual(analysis['safety_score'], 100)
        self.assertIn('domain_scores', analysis)
        self.assertIn('Violent Crimes', analysis['domain_scores'])
        self.assertIn('benchmark_text', analysis)
        print(f"[PASS] Mumbai Safety Score: {analysis['safety_score']}/100 | Domain Scores: {analysis['domain_scores']}")

    def test_04_map_data_endpoint(self):
        """M2.2: Verify /api/map-data returns coordinates & safety scores for Leaflet."""
        res = self.client.get('/api/map-data')
        self.assertEqual(res.status_code, 200)
        points = json.loads(res.data.decode('utf-8'))
        self.assertIsInstance(points, list)
        self.assertGreater(len(points), 10)
        first = points[0]
        self.assertIn('name', first)
        self.assertIn('lat', first)
        self.assertIn('lng', first)
        self.assertIn('safety_score', first)
        print(f"[PASS] /api/map-data returned {len(points)} geographic hubs with safety metrics")

    def test_05_compare_route_and_engine(self):
        """M2.4: Verify side-by-side comparison between Mumbai and Pune."""
        res = self.client.get('/compare?loc1=Mumbai&loc2=Pune')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Mumbai", html)
        self.assertIn("Pune", html)
        self.assertIn("Safety Sub-Index Comparison", html)
        self.assertIn("Multi-Year Trajectory Overlay", html)
        print("[PASS] /compare?loc1=Mumbai&loc2=Pune rendered comparative dashboard")

    def test_06_prediction_confidence_intervals(self):
        """S2.2: Verify ARIMA 90% confidence interval bands are computed."""
        pred = self.predictor.predict_crimes('DELHI UT')
        self.assertIsNotNone(pred)
        self.assertIn('conf_intervals', pred)
        conf = pred['conf_intervals']
        self.assertIsNotNone(conf)
        self.assertIn('lower', conf)
        self.assertIn('upper', conf)
        self.assertEqual(len(conf['lower']), len(pred['YEAR']))
        self.assertEqual(len(conf['upper']), len(pred['YEAR']))
        for low, high in zip(conf['lower'], conf['upper']):
            self.assertLessEqual(low, high, "Lower confidence bound exceeded upper bound!")
        print(f"[PASS] Delhi Forecast: {pred['TOTAL IPC CRIMES']} | 90% Confidence Lower: {conf['lower']}, Upper: {conf['upper']}")

if __name__ == '__main__':
    unittest.main()
