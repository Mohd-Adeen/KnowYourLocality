import os
import json
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, Response
from crime_analysis import CrimeAnalyzer
from crime_prediction import CrimePredictor
from database_manager import DatabaseManager

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey123')

# Initialize modules with cleaned official NCRB government dataset
DATA_PATH = 'crime_data_clean.csv' if os.path.exists('crime_data_clean.csv') else 'crime_data.csv'
analyzer = CrimeAnalyzer(DATA_PATH)
predictor = CrimePredictor(DATA_PATH)
db_manager = DatabaseManager()

# Key hubs for interactive geographic safety map
MAP_HUBS = [
    {"name": "Mumbai", "lat": 18.9220, "lng": 72.8347},
    {"name": "Pune", "lat": 18.5204, "lng": 73.8567},
    {"name": "Delhi UT", "label": "Delhi", "lat": 28.6139, "lng": 77.2090},
    {"name": "Bangalore Commr.", "label": "Bangalore", "lat": 12.9716, "lng": 77.5946},
    {"name": "Hyderabad City", "label": "Hyderabad", "lat": 17.3850, "lng": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lng": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lng": 88.3639},
    {"name": "Ahmedabad Commr.", "label": "Ahmedabad", "lat": 23.0225, "lng": 72.5714},
    {"name": "Jaipur", "lat": 26.9124, "lng": 75.7873},
    {"name": "Lucknow", "lat": 26.8467, "lng": 80.9462},
    {"name": "Patna", "lat": 25.5941, "lng": 85.1376},
    {"name": "Bhopal", "lat": 23.2599, "lng": 77.4126},
    {"name": "Chandigarh", "lat": 30.7333, "lng": 76.7794},
    {"name": "Nagpur", "lat": 21.1458, "lng": 79.0882},
    {"name": "Indore", "lat": 22.7196, "lng": 75.8577},
    {"name": "Varanasi", "lat": 25.3176, "lng": 82.9739},
    {"name": "Surat", "lat": 21.1702, "lng": 72.8311},
    {"name": "Visakhapatnam", "lat": 17.6868, "lng": 83.2185},
    {"name": "Goa", "lat": 15.2993, "lng": 74.1240},
    {"name": "Ludhiana", "lat": 30.9010, "lng": 75.8573}
]

@app.route('/')
def index():
    heatmap_data = analyzer.get_state_crime_heatmap_data()
    return render_template('index.html', heatmap_summary=heatmap_data['summary'], heatmap_points=heatmap_data['points'])

@app.route('/autocomplete')
def autocomplete():
    """
    Search suggestion endpoint returning matching states and districts.
    """
    q = request.args.get('q', '').strip().upper()
    if len(q) < 2:
        return jsonify([])

    states = [s for s in analyzer.df['STATE'].unique() if s]
    districts = [d for d in analyzer.df[~analyzer.df['IS_AGGREGATE_ROW']]['DISTRICT'].unique() if d]
    all_locations = sorted(list(set(states + districts)))

    matches = [loc.title() for loc in all_locations if q in loc]
    return jsonify(matches[:10])

@app.route('/api/locations')
def get_locations():
    """
    Returns sanitized list of states and non-aggregate districts.
    """
    states = sorted([s.title() for s in analyzer.df['STATE'].unique() if s])
    districts = sorted([d.title() for d in analyzer.df[~analyzer.df['IS_AGGREGATE_ROW']]['DISTRICT'].unique() if d])
    return jsonify({"states": states, "districts": districts})

@app.route('/api/map-data')
def get_map_data():
    """
    Phase 2: State-wise crime rate heatmap data endpoint for Leaflet.
    Calculates average crime rate per 100k, population normalization,
    and heat intensity for all 35 States & Union Territories of India.
    """
    heatmap_data = analyzer.get_state_crime_heatmap_data()
    return jsonify(heatmap_data['points'])

@app.route('/api/heatmap-summary')
def get_heatmap_summary():
    """
    Returns calculated national average statistics and state heat extremes.
    """
    heatmap_data = analyzer.get_state_crime_heatmap_data()
    return jsonify(heatmap_data['summary'])

@app.route('/search', methods=['POST'])
def search():
    location = request.form.get('location', '').strip()
    if not location:
        flash('Please enter a location name')
        return redirect(url_for('index'))

    location_data = analyzer.get_location_data(location)
    if not location_data:
        flash(f'Location "{location}" not found in our database')
        return redirect(url_for('index'))

    analysis_data = analyzer.generate_crime_analysis(location)
    if not analysis_data:
        flash("Could not generate analysis data.")
        return redirect(url_for('index'))

    trend_fig = analyzer.create_crime_trends_plot(analysis_data)
    trend_json = json.loads(trend_fig.to_json())
    is_saved = db_manager.is_location_saved(analysis_data['location'])

    return render_template(
        'analysis.html',
        location=analysis_data['location'],
        state_name=analysis_data['state_name'],
        location_type=analysis_data['type'],
        population=f"{analysis_data['population']:,}",
        avg_annual_crimes=f"{analysis_data['avg_annual_crimes']:,}",
        crime_rate_per_100k=analysis_data['crime_rate_per_100k'],
        safety_score=analysis_data['safety_score'],
        domain_scores=analysis_data['domain_scores'],
        benchmark_text=analysis_data['benchmark_text'],
        benchmark_class=analysis_data['benchmark_class'],
        risk_level=analysis_data['risk_level'],
        risk_color=analysis_data['risk_color'],
        safety_badge_class=analysis_data['safety_badge_class'],
        domain_breakdown=analysis_data['domain_breakdown'],
        period=analysis_data['period'],
        trend_json=trend_json,
        is_saved=is_saved
    )

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        location = request.form.get('location') or (request.json and request.json.get('location')) or ''
        location = str(location).strip().upper()

        if not location:
            error_msg = "Please enter a location name"
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': error_msg}), 400
            return render_template('prediction.html', error=error_msg)

        predictions = predictor.predict_crimes(location)
        if not predictions:
            error_msg = f'Location "{location.title()}" not found or insufficient historical data.'
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': error_msg}), 404
            return render_template('prediction.html', error=error_msg)

        future_years = predictions['YEAR']
        chart_html = predictor.generate_arima_chart(predictor.df, predictions, future_years)
        crime_indicator = predictor.calculate_crime_indicator(location)
        diagnostics = predictor.evaluate_model_performance(location)

        prediction_data = {
            "location": location.title(),
            "years": future_years,
            "predictions": {
                k: v for k, v in predictions.items() 
                if k not in ["YEAR", "historical_years", "historical_totals", "location_type", "state_name", "conf_intervals"]
            }
        }

        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "location": prediction_data['location'],
                "years": future_years,
                "predictions": prediction_data['predictions'],
                "crime_indicator": crime_indicator,
                "chart_html": chart_html,
                "diagnostics": diagnostics
            })

        return render_template(
            'prediction.html',
            prediction=prediction_data,
            chart_html=chart_html,
            crime_indicator=crime_indicator,
            diagnostics=diagnostics
        )

    return render_template('prediction.html')

@app.route('/rankings')
def rankings():
    """
    Phase 3: National & State District Rankings & Hotspot Discovery Dashboard.
    """
    state = request.args.get('state', '').strip()
    domain = request.args.get('domain', '').strip()
    sort = request.args.get('sort', 'safest').strip()
    rankings_data = analyzer.get_rankings_data(state=state, domain=domain, sort=sort, limit=60)
    return render_template('rankings.html', rankings=rankings_data)

@app.route('/report/<location>')
def locality_report(location):
    """
    Phase 3: Comprehensive printable/PDF-ready Locality Safety Dossier.
    """
    analysis = analyzer.generate_crime_analysis(location)
    if not analysis:
        flash(f'Location "{location}" not found')
        return redirect(url_for('index'))

    predictions = predictor.predict_crimes(location)
    diagnostics = predictor.evaluate_model_performance(location)
    is_saved = db_manager.is_location_saved(analysis['location'])
    feedback = db_manager.get_feedback_for_location(analysis['location'])

    return render_template(
        'report.html',
        analysis=analysis,
        prediction=predictions,
        diagnostics=diagnostics,
        is_saved=is_saved,
        feedback=feedback
    )

@app.route('/export/csv/<location>')
def export_csv(location):
    """
    Phase 3: Export multi-year historical crime data as downloadable CSV.
    """
    csv_content = analyzer.generate_csv_data(location)
    if not csv_content:
        flash(f'Could not generate CSV for "{location}"')
        return redirect(url_for('index'))

    safe_filename = location.strip().replace(' ', '_').lower()
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={safe_filename}_crime_data.csv'}
    )

@app.route('/export/forecast-csv/<location>')
def export_forecast_csv(location):
    """
    Phase 3: Export 2027-2030 ARIMA forecast series as downloadable CSV.
    """
    csv_content = predictor.generate_forecast_csv(location)
    if not csv_content:
        flash(f'Could not generate forecast CSV for "{location}"')
        return redirect(url_for('predict'))

    safe_filename = location.strip().replace(' ', '_').lower()
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={safe_filename}_forecast_2027_2030.csv'}
    )

@app.route('/api/bookmarks', methods=['GET', 'POST', 'DELETE'])
def bookmarks():
    """
    Phase 3: Manage saved/bookmarked localities in SQLite database.
    """
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        location = data.get('location', '').strip()
        if not location:
            return jsonify({'success': False, 'error': 'Missing location'}), 400
        analysis = analyzer.generate_crime_analysis(location)
        score = analysis['safety_score'] if analysis else None
        rate = analysis['crime_rate_per_100k'] if analysis else None
        db_manager.save_location(location, score, rate)
        return jsonify({'success': True, 'saved': True, 'location': location.title()})

    elif request.method == 'DELETE':
        data = request.get_json(silent=True) or request.args
        location = data.get('location', '').strip()
        db_manager.remove_saved_location(location)
        return jsonify({'success': True, 'saved': False})

    # GET
    saved = db_manager.get_saved_locations()
    return jsonify({'bookmarks': saved})

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Phase 3: Citizen community safety observation submission.
    """
    data = request.get_json(silent=True) or request.form
    location = data.get('location', '').strip()
    category = data.get('category', 'General Safety').strip()
    comment = data.get('comment', '').strip()

    if not location or not comment:
        return jsonify({'success': False, 'error': 'Location and comment are required.'}), 400

    db_manager.submit_feedback(location, category, comment)
    return jsonify({'success': True, 'message': 'Feedback received. Thank you for contributing to civic safety!'})

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    """
    Phase 2: Side-by-side locality comparison engine.
    """
    loc1 = request.args.get('loc1') or (request.form and request.form.get('loc1')) or ''
    loc2 = request.args.get('loc2') or (request.form and request.form.get('loc2')) or ''

    loc1 = loc1.strip()
    loc2 = loc2.strip()

    comparison = None
    error = None

    if loc1 and loc2:
        res = analyzer.compare_locations(loc1, loc2)
        if res:
            comparison = res
        else:
            error = f"Could not compare '{loc1}' and '{loc2}'. Please ensure both location names are valid."

    return render_template('compare.html', loc1=loc1, loc2=loc2, comparison=comparison, error=error)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', 'Friend')
        email = request.form.get('email', '')
        message = request.form.get('message', '')
        db_manager.save_contact_message(name, email, message)
        flash(f'Thank you, {name}! Your message has been received. Our team will review your inquiry shortly.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)