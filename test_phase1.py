"""
Automated Validation Suite for Phase 1 Implementation
------------------------------------------------------
Tests data integrity, per-capita normalization, endpoint contracts,
ARIMA forecasting stability, and caching.
"""

import unittest
import json
import time
from app import app
from crime_analysis import CrimeAnalyzer
from crime_prediction import CrimePredictor
from fetch_government_data import get_population_for_location

class Phase1ValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.analyzer = CrimeAnalyzer('crime_data_clean.csv')
        cls.predictor = CrimePredictor('crime_data_clean.csv')

    def test_01_no_aggregate_rows_in_districts(self):
        """M1.1: Verify 'TOTAL' rows are not treated as valid districts."""
        clean_districts = self.analyzer.df[~self.analyzer.df['IS_AGGREGATE_ROW']]['DISTRICT'].unique()
        for d in clean_districts:
            self.assertNotEqual(d, 'TOTAL', "Aggregate 'TOTAL' found in district list!")
            self.assertFalse('TOTAL' in d and 'DELHI' not in d, f"Suspicious total district: {d}")

    def test_02_population_normalization(self):
        """M1.2: Verify population lookup and per-capita rate calculation."""
        pop_mh = get_population_for_location('MAHARASHTRA', 'state')
        self.assertEqual(pop_mh, 112374333)

        analysis = self.analyzer.generate_crime_analysis('MAHARASHTRA')
        self.assertIsNotNone(analysis)
        self.assertIn('crime_rate_per_100k', analysis)
        self.assertIn('population', analysis)
        self.assertGreater(analysis['crime_rate_per_100k'], 0)
        self.assertLess(analysis['crime_rate_per_100k'], 1000)
        print(f"\n[PASS] Maharashtra Crime Rate: {analysis['crime_rate_per_100k']} per 100k citizens (Risk: {analysis['risk_level']})")

    def test_03_district_analysis_mumbai(self):
        """Verify district level analysis for Mumbai."""
        analysis = self.analyzer.generate_crime_analysis('MUMBAI')
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis['type'], 'district')
        self.assertIn('domain_breakdown', analysis)
        self.assertIn('Violent Crimes', analysis['domain_breakdown'])
        print(f"[PASS] Mumbai Analysis: Pop={analysis['population']:,}, Avg Annual Crimes={analysis['avg_annual_crimes']:,}, Rate={analysis['crime_rate_per_100k']}/100k")

    def test_04_prediction_state_aggregation(self):
        """M1.5: Verify state-level prediction uses clean year-aggregated series."""
        pred = self.predictor.predict_crimes('MAHARASHTRA')
        self.assertIsNotNone(pred)
        self.assertEqual(len(pred['YEAR']), 4)
        self.assertIn('TOTAL IPC CRIMES', pred)
        self.assertEqual(len(pred['TOTAL IPC CRIMES']), 4)

        # Test caching speed
        t0 = time.time()
        cached_pred = self.predictor.predict_crimes('MAHARASHTRA')
        duration = time.time() - t0
        self.assertLess(duration, 0.05, f"Cache retrieval was too slow: {duration}s")
        print(f"[PASS] Maharashtra 3-Year Forecast: {pred['YEAR']} -> {pred['TOTAL IPC CRIMES']} (Cached in {duration*1000:.2f}ms)")

    def test_05_autocomplete_endpoint(self):
        """M1.4: Verify /autocomplete endpoint contract."""
        res = self.client.get('/autocomplete?q=Mum')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertTrue(any('Mumbai' in item for item in data))
        print(f"[PASS] Autocomplete for 'Mum': {data}")

    def test_06_api_locations_endpoint(self):
        """M1.4: Verify /api/locations excludes 'TOTAL'."""
        res = self.client.get('/api/locations')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode('utf-8'))
        self.assertIn('states', data)
        self.assertIn('districts', data)
        self.assertNotIn('Total', data['districts'])
        print(f"[PASS] Locations API: {len(data['states'])} states, {len(data['districts'])} districts")

    def test_07_search_post_route(self):
        """Verify POST /search renders analysis page with per-capita metrics."""
        res = self.client.post('/search', data={'location': 'Pune'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Pune', html)
        self.assertIn('Crime Rate (per 100k)', html)
        self.assertIn('Census 2011 Population', html)
        print(f"[PASS] Search POST /search for 'Pune' returned 200 with new per-capita metrics")

    def test_08_predict_ajax_and_form(self):
        """Verify POST /predict handles both form and AJAX JSON."""
        # Test JSON AJAX
        res_json = self.client.post('/predict', 
                                    data=json.dumps({'location': 'PUNE'}), 
                                    content_type='application/json')
        self.assertEqual(res_json.status_code, 200)
        data = json.loads(res_json.data.decode('utf-8'))
        self.assertIn('predictions', data)
        self.assertIn('crime_indicator', data)
        self.assertIn('chart_html', data)
        print(f"[PASS] AJAX /predict returned JSON with indicator: {data['crime_indicator']}")

if __name__ == '__main__':
    unittest.main()
