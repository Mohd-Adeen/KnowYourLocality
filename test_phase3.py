"""
Phase 3 Validation Test Suite
------------------------------
Tests:
1. M3.1: Export & Citizen Safety Dossier Engine:
   - GET /export/csv/<location> returns valid CSV attachment.
   - GET /export/forecast-csv/<location> returns 2025-2028 forecast CSV.
   - GET /report/<location> renders comprehensive printable Locality Safety Dossier.
2. M3.2: District & Hotspot Rankings Dashboard:
   - analyzer.get_rankings_data() computes per-capita crime rates & safety scores.
   - Supports State and Domain filtering.
   - GET /rankings returns 200 OK with ranked administrative district directory.
3. M3.3: Database Persistence & Feedback Engine:
   - SQLite tables initialized (contact_messages, saved_locations, safety_feedback).
   - POST /contact saves message in DB.
   - POST /api/bookmarks, GET /api/bookmarks, DELETE /api/bookmarks manage saved localities.
   - POST /api/feedback records citizen community safety observations.
4. M3.4: Predictive Model Diagnostics & Comparison Engine:
   - predictor.evaluate_model_performance() calculates holdout MAE, RMSE, MAPE, and Accuracy %.
   - prediction.html renders diagnostics card.
"""

import unittest
import json
import io
from app import app, db_manager
from crime_analysis import CrimeAnalyzer
from crime_prediction import CrimePredictor

class Phase3ValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.analyzer = CrimeAnalyzer('crime_data_clean.csv')
        cls.predictor = CrimePredictor('crime_data_clean.csv')

    def test_01_rankings_engine_and_route(self):
        """M3.2: Verify District Rankings calculation and /rankings route."""
        # 1. National Rankings
        all_rankings = self.analyzer.get_rankings_data(limit=25)
        self.assertIsNotNone(all_rankings)
        self.assertIn('districts', all_rankings)
        self.assertGreater(len(all_rankings['districts']), 10)
        first_dist = all_rankings['districts'][0]
        self.assertIn('district', first_dist)
        self.assertIn('state', first_dist)
        self.assertIn('crime_rate_per_100k', first_dist)
        self.assertIn('safety_score', first_dist)

        # 2. State Filter
        mh_rankings = self.analyzer.get_rankings_data(state='MAHARASHTRA', limit=20)
        self.assertTrue(all(d['state'] == 'Maharashtra' for d in mh_rankings['districts']))

        # 3. Domain Filter
        women_rankings = self.analyzer.get_rankings_data(domain="Women's Safety", limit=15)
        self.assertEqual(women_rankings['current_domain'], "Women's Safety")

        # 4. HTTP Route
        res = self.client.get('/rankings?state=MAHARASHTRA&sort=safest')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Crime Rankings", html)
        self.assertIn("Maharashtra", html)
        self.assertIn("Ranked District Directory", html)
        print(f"\n[PASS] M3.2: Rankings Engine verified. Top Safest in Maharashtra: {mh_rankings['districts'][0]['district']} (Rate: {mh_rankings['districts'][0]['crime_rate_per_100k']}/100k)")

    def test_02_csv_exports(self):
        """M3.1: Verify historical and forecast CSV export endpoints."""
        # 1. Historical CSV Export
        res_hist = self.client.get('/export/csv/Mumbai')
        self.assertEqual(res_hist.status_code, 200)
        self.assertEqual(res_hist.mimetype, 'text/csv')
        csv_text = res_hist.data.decode('utf-8')
        lines = csv_text.strip().splitlines()
        self.assertGreater(len(lines), 5)
        headers = lines[0].split(',')
        self.assertIn('LOCATION', headers)
        self.assertIn('YEAR', headers)
        self.assertIn('TOTAL IPC CRIMES', headers)
        self.assertIn('CRIME_RATE_PER_100K', headers)
        self.assertIn('SAFETY_SCORE_INDEX', headers)

        # 2. Forecast CSV Export
        res_pred = self.client.get('/export/forecast-csv/Mumbai')
        self.assertEqual(res_pred.status_code, 200)
        self.assertEqual(res_pred.mimetype, 'text/csv')
        pred_csv = res_pred.data.decode('utf-8')
        pred_lines = pred_csv.strip().splitlines()
        self.assertEqual(len(pred_lines), 5)  # Header + 4 forecasted years (2025-2028)
        pred_headers = pred_lines[0].split(',')
        self.assertIn('PROJECTED_TOTAL_IPC_CRIMES', pred_headers)
        self.assertIn('CONFIDENCE_LOWER_90', pred_headers)
        self.assertIn('CONFIDENCE_UPPER_90', pred_headers)

        print("[PASS] M3.1: CSV Export verified for historical incidents and 2025-2028 forecast series")

    def test_03_locality_safety_dossier_report(self):
        """M3.1: Verify /report/<location> renders comprehensive printable dossier."""
        res = self.client.get('/report/Mumbai')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        self.assertIn("Official Locality Safety Dossier", html)
        self.assertIn("Mumbai", html)
        self.assertIn("Safety Score Index", html)
        self.assertIn("4-Year Statistical Trend Forecast", html)
        self.assertIn("Safety Domain Breakdown", html)
        self.assertIn("Verified Citizen Emergency Directory", html)
        self.assertIn("112", html)
        self.assertIn("window.print()", html)
        print("[PASS] M3.1: Locality Safety Dossier (/report/Mumbai) rendered successfully with printable layout")

    def test_04_database_persistence(self):
        """M3.3: Verify SQLite database persistence for contact, bookmarks, and feedback."""
        # 1. Contact Message Persistence
        res_post = self.client.post('/contact', data={
            'name': 'Test Citizen',
            'email': 'citizen@safety.gov.in',
            'message': 'Testing Phase 3 database persistence'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)

        recent_msgs = db_manager.get_contact_messages(limit=5)
        self.assertTrue(any(m['name'] == 'Test Citizen' for m in recent_msgs))

        # 2. Bookmarks / Saved Locations
        # Save bookmark
        res_save = self.client.post('/api/bookmarks', json={'location': 'Pune'})
        self.assertEqual(res_save.status_code, 200)
        self.assertTrue(json.loads(res_save.data.decode('utf-8'))['saved'])
        self.assertTrue(db_manager.is_location_saved('Pune'))

        # Fetch bookmarks
        res_list = self.client.get('/api/bookmarks')
        saved_list = json.loads(res_list.data.decode('utf-8'))['bookmarks']
        self.assertTrue(any(b['location'] == 'Pune' for b in saved_list))

        # Delete bookmark
        res_del = self.client.delete('/api/bookmarks', json={'location': 'Pune'})
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(db_manager.is_location_saved('Pune'))

        # 3. Community Safety Feedback
        res_fb = self.client.post('/api/feedback', json={
            'location': 'Mumbai',
            'category': 'Police Patrolling',
            'comment': 'High police presence observed around station area'
        })
        self.assertEqual(res_fb.status_code, 200)
        fb_list = db_manager.get_feedback_for_location('Mumbai')
        self.assertTrue(len(fb_list) > 0)

        print("[PASS] M3.3: Database Persistence verified for Contact Messages, Saved Localities, and Safety Feedback")

    def test_05_predictive_model_diagnostics(self):
        """M3.4: Verify ARIMA vs Baseline model evaluation metrics."""
        diag = self.predictor.evaluate_model_performance('DELHI UT')
        self.assertIsNotNone(diag)
        self.assertIn('arima', diag)
        self.assertIn('baseline', diag)
        self.assertIn('accuracy_pct', diag['arima'])
        self.assertGreaterEqual(diag['arima']['accuracy_pct'], 75.0)
        self.assertIn('rmse', diag['arima'])
        self.assertIn('mae', diag['arima'])
        self.assertIn('better_model', diag)

        # HTTP Prediction page includes diagnostics
        res = self.client.post('/predict', data={'location': 'Delhi UT'})
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Statistical Model Diagnostics", html)
        self.assertIn("Model Fit Accuracy", html)
        print(f"[PASS] M3.4: Predictive Diagnostics verified: ARIMA Accuracy={diag['arima']['accuracy_pct']}%, RMSE={diag['arima']['rmse']}, Best Model={diag['better_model']}")

if __name__ == '__main__':
    unittest.main()
