from flask import Flask, request, render_template, render_template_string, redirect, url_for, flash, jsonify
from crime_analysis import CrimeAnalyzer
from crime_prediction import CrimePredictor
from markupsafe import Markup
import plotly.io as pio
import mysql.connector
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

# Initialize modules
analyzer = CrimeAnalyzer('crime_data.csv')
predictor = CrimePredictor('crime_data.csv')

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'crime_analysis'
}

@app.route('/')
def index():
    return render_template('index.html')


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
    
    # Generate analysis data
    analysis_data = analyzer.generate_crime_analysis(location)  # ✅ Correct method call
    if not analysis_data:
        flash("Could not generate analysis data.")
        return redirect(url_for('index'))
    
    # Generate plot
    trend_fig = analyzer.create_crime_trends_plot(analysis_data)
    trend_json = json.loads(trend_fig.to_json())

    # Debugging: Log trend_json before rendering the template
    print(f"Generated trend_json: {trend_json}")  # Log to console

    return render_template('analysis.html',
                           location=analysis_data['location'],
                           location_type=location_data['type'],
                           trend_json=trend_json,
                           risk_level=analysis_data['risk_level'],
                           risk_color=analysis_data['risk_color'])  # Pass data for the plot correctly


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        location = request.form.get('location', '').strip().upper()

        predictions = predictor.predict_crimes(location)

        if not predictions:
            return render_template('prediction.html', error="Location not found or not enough data")

        future_years = predictions['YEAR']
        chart_html = predictor.generate_arima_chart(predictor.df, predictions, future_years)

        # Calculate the crime indicator for the given location
        crime_indicator = predictor.calculate_crime_indicator(location)

        # This matches what prediction.html is trying to access
        prediction_data = {
            "location": location,
            "years": future_years,
            "predictions": {k: v for k, v in predictions.items() if k != "YEAR"}
        }

        return render_template(
            'prediction.html',
            prediction=prediction_data,
            chart_html=chart_html,
            crime_indicator=crime_indicator  # Pass the crime indicator to the template
        )

    # For GET request: just render the prediction page without results
    return render_template('prediction.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/api/locations')
def get_locations():
    states = analyzer.df['STATE'].unique().tolist()
    districts = analyzer.df['DISTRICT'].unique().tolist()
    return jsonify({"states": states, "districts": districts})

if __name__ == '__main__':
    app.run(debug=True)