import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
import plotly.graph_objects as go

class CrimePredictor:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.df.columns = self.df.columns.str.upper().str.strip()

        # Identify crime-related columns
        self.crime_columns = [col for col in self.df.columns if col not in ['STATE', 'DISTRICT', 'YEAR', 'TOTAL IPC CRIMES']]

        # Clean: Ensure numeric types for all crime columns
        self.df[self.crime_columns] = self.df[self.crime_columns].apply(pd.to_numeric, errors='coerce').fillna(0)

    def predict_crimes(self, location):
        location = location.strip().upper()

        # First check in STATE
        location_data = self.df[self.df['STATE'] == location]
        if location_data.empty:
            # Then check in DISTRICT
            location_data = self.df[self.df['DISTRICT'] == location]

        if location_data.empty:
            return None  # No match found

        predictions = {}
        future_years = []

        for crime in self.crime_columns:
            crime_series = pd.to_numeric(location_data[crime], errors='coerce').dropna()

            if len(crime_series) < 10:  # Require enough data points
                continue

            try:
                model = ARIMA(crime_series, order=(5, 1, 0))
                model_fit = model.fit()
                forecast = model_fit.forecast(steps=3)
                predictions[crime] = forecast.tolist()
                future_years = list(range(location_data['YEAR'].max() + 1, location_data['YEAR'].max() + 4))
            except Exception as e:
                print(f"Error in ARIMA for {crime}: {e}")
                continue

        return {
            'YEAR': future_years,
            **predictions
        }
    
    def calculate_crime_indicator(self, location):
        location = location.strip().upper()

        # Get the location data
        location_data = self.df[self.df['STATE'] == location]
        if location_data.empty:
            location_data = self.df[self.df['DISTRICT'] == location]

        if location_data.empty:
            return "Location not found"

        # Calculate the total crime count for the location
        total_crimes = location_data[self.crime_columns].sum().sum()  # Sum across all crime columns

        # Define crime indicator logic based on the total crime count
        if total_crimes < 1000:
            return "Low Risk"
        elif 1000 <= total_crimes < 5000:
            return "Medium Risk"
        else:
            return "High Risk"

    def generate_arima_chart(self, df, predictions, future_years):
        fig = go.Figure()

        for crime, values in predictions.items():
            if crime == 'YEAR':
                continue
            fig.add_trace(go.Scatter(
                x=future_years,
                y=values,
                mode='lines+markers',
                name=crime
            ))

        fig.update_layout(
            title='Crime Forecast (Next 3 Years)',
            xaxis_title='Year',
            yaxis_title='Predicted Crime Count',
            template='plotly_white'
        )

        return fig.to_html(full_html=False)
