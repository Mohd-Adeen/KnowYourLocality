"""
State-wise Crime Rate Heatmap Validation Test Suite
----------------------------------------------------
Tests:
1. Verification of state crime rate calculations across all 35 States & UTs.
2. Verification of Census 2011 population normalization.
3. Verification of normalized heat intensity scaling.
4. Validation of /api/map-data endpoint for Leaflet heatmap.
5. Validation of /api/heatmap-summary endpoint for KPI statistics.
6. Verification that landing page renders with state heatmap components.
"""

import unittest
import json
from app import app
from crime_analysis import CrimeAnalyzer, STATE_COORDINATES

class StateHeatmapValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.analyzer = CrimeAnalyzer('crime_data_clean.csv')

    def test_01_all_35_states_mapped_with_coordinates(self):
        """Ensure all 35 states in the dataset have valid geographic coordinates."""
        dataset_states = set(self.analyzer.df['STATE'].unique())
        self.assertEqual(len(dataset_states), 35)
        for state in dataset_states:
            self.assertIn(state, STATE_COORDINATES, f"State {state} missing from STATE_COORDINATES")
            coords = STATE_COORDINATES[state]
            self.assertIn('lat', coords)
            self.assertIn('lng', coords)
            self.assertGreater(coords['lat'], 5.0, f"Invalid latitude for {state}")
            self.assertLess(coords['lat'], 38.0, f"Invalid latitude for {state}")
            self.assertGreater(coords['lng'], 68.0, f"Invalid longitude for {state}")
            self.assertLess(coords['lng'], 98.0, f"Invalid longitude for {state}")
        print(f"\n[PASS] All {len(dataset_states)} States & UTs have valid coordinates")

    def test_02_average_crime_rate_and_heat_calculation(self):
        """Verify state-wise average crime rate and heat intensity calculations."""
        data = self.analyzer.get_state_crime_heatmap_data()
        self.assertIn('points', data)
        self.assertIn('summary', data)
        self.assertEqual(len(data['points']), 35)

        summary = data['summary']
        self.assertIn('national_weighted_avg', summary)
        self.assertGreater(summary['national_weighted_avg'], 100)
        self.assertIn('min_rate', summary)
        self.assertIn('max_rate', summary)
        self.assertLess(summary['min_rate'], summary['max_rate'])

        for pt in data['points']:
            # Verify calculations
            self.assertIn('name', pt)
            self.assertIn('crime_rate_per_100k', pt)
            self.assertGreater(pt['crime_rate_per_100k'], 0)
            self.assertIn('avg_annual_crimes', pt)
            self.assertGreater(pt['avg_annual_crimes'], 0)
            self.assertIn('heat_intensity', pt)
            self.assertGreaterEqual(pt['heat_intensity'], 0.20)
            self.assertLessEqual(pt['heat_intensity'], 1.00)
            self.assertIn('heat_level', pt)
            self.assertIn(pt['heat_level'], ['Low Heat', 'Moderate Heat', 'High Heat', 'Severe Heat'])
            self.assertIn('safety_score', pt)
            self.assertGreaterEqual(pt['safety_score'], 0)
            self.assertLessEqual(pt['safety_score'], 100)

        print(f"[PASS] State crime rate calculations verified: Min={summary['min_rate']} ({summary['lowest_state']}), Max={summary['max_rate']} ({summary['highest_state']}), National Avg={summary['national_weighted_avg']}/100k")

    def test_03_map_data_endpoint(self):
        """Verify /api/map-data returns 35 states with heat metrics."""
        res = self.client.get('/api/map-data')
        self.assertEqual(res.status_code, 200)
        points = json.loads(res.data.decode('utf-8'))
        self.assertIsInstance(points, list)
        self.assertEqual(len(points), 35)

        # Check required fields for leaflet heatmap & circle markers
        for pt in points:
            self.assertIn('name', pt)
            self.assertIn('lat', pt)
            self.assertIn('lng', pt)
            self.assertIn('crime_rate_per_100k', pt)
            self.assertIn('heat_intensity', pt)
            self.assertIn('heat_level', pt)
            self.assertIn('heat_color', pt)
            self.assertIn('safety_score', pt)

        print(f"[PASS] /api/map-data returned {len(points)} state heatmap records with 200 OK")

    def test_04_heatmap_summary_endpoint(self):
        """Verify /api/heatmap-summary returns accurate aggregation stats."""
        res = self.client.get('/api/heatmap-summary')
        self.assertEqual(res.status_code, 200)
        summary = json.loads(res.data.decode('utf-8'))
        self.assertEqual(summary['total_states'], 35)
        self.assertEqual(summary['lowest_state'], 'Nagaland')
        self.assertAlmostEqual(summary['lowest_state_rate'], 99.34, places=1)
        self.assertEqual(summary['highest_state'], 'Delhi')
        print(f"[PASS] /api/heatmap-summary verified: {summary}")

    def test_05_landing_page_renders_heatmap(self):
        """Verify landing page renders with state heatmap components and script."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        self.assertIn("State-wise Crime Rate Heatmap of India", html)
        self.assertIn("National Avg Crime Rate", html)
        self.assertIn("Heat Intensity Scale", html)
        self.assertIn("localityMap", html)
        self.assertIn("leaflet-heat.js", html)
        self.assertIn("btnToggleHeat", html)
        self.assertIn("btnToggleMarkers", html)
        self.assertIn("btnResetView", html)
        self.assertIn("stateRankingsTable", html)
        print("[PASS] Landing page renders state heatmap section, controls, and rankings table successfully")

if __name__ == '__main__':
    unittest.main()
