import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class CrimeAnalyzer:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path, header=0)
        self.crime_columns = [col for col in self.df.columns 
                            if col not in ['STATE', 'DISTRICT', 'YEAR', 'TOTAL IPC CRIMES']]
        self._clean_data()
        self._prepare_melted_data()
    
    """def _clean_data(self):
        self.df.columns = self.df.columns.str.strip().str.upper()
        self.df['STATE'] = self.df['STATE'].astype(str).str.strip().str.upper()
        self.df['DISTRICT'] = self.df['DISTRICT'].astype(str).str.strip().str.upper()
        for col in self.df.columns:
            if col not in ['STATE', 'DISTRICT', 'YEAR']:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)"""
    
    def _clean_data(self):
        """Standardize data formatting"""
        if 'STATE' not in self.df.columns or 'DISTRICT' not in self.df.columns or 'YEAR' not in self.df.columns:
            print("ERROR: 'STATE', 'DISTRICT', or 'YEAR' columns are missing!")
        return  # Handle the error gracefully

        self.df.columns = self.df.columns.str.strip().str.upper()
        self.df['STATE'] = self.df['STATE'].astype(str).str.strip().str.upper()
        self.df['DISTRICT'] = self.df['DISTRICT'].astype(str).str.strip().str.upper()
        for col in self.df.columns:
            if col not in ['STATE', 'DISTRICT', 'YEAR']:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

    
    def _prepare_melted_data(self):
        """Create melted version of the data"""
        self.melted_df = self.df.melt(
            id_vars=['STATE', 'DISTRICT', 'YEAR'],
            value_vars=self.crime_columns,
            var_name='CRIME_TYPE',
            value_name='CASES'
        )
    
    def get_location_data(self, location):
        """Get data for specific location"""
        location = str(location).strip().upper()
        
        # Search in STATE column
        state_data = self.df[self.df['STATE'] == location]
        if not state_data.empty:
            return {
                'type': 'state',
                'data': state_data,
                'melted': self.melted_df[self.melted_df['STATE'] == location]
            }
        
        # Search in DISTRICT column
        district_data = self.df[self.df['DISTRICT'] == location]
        if not district_data.empty:
            return {
                'type': 'district',
                'data': district_data,
                'melted': self.melted_df[self.melted_df['DISTRICT'] == location]
            }
        
        return None
    
    def analyze_location(self, location):
        """Main analysis method to be called from Flask"""
        loc_data = self.get_location_data(location)
        if not loc_data:
            return None
            
        return self.generate_crime_analysis(loc_data)
    
    def generate_crime_analysis(self, location):
        location_data = self.get_location_data(location)
    
        if location_data is None:
            return None  # or handle gracefully
    
        # Accessing the 'data' DataFrame properly
        location_df = location_data['data']
    
        # Check if we are dealing with 'state' or 'district'
        location_type = 'state' if (location_df['STATE'] == location.upper()).any() else 'district'
    
        # Group by year and sum the crime columns for yearly trends
        yearly_data = location_df.groupby('YEAR')[self.crime_columns].sum().reset_index()
    
        # Calculate the percentage change between years for each crime
        pct_change = yearly_data[self.crime_columns].pct_change() * 100

        # Compute average total crimes per year
        total_crime_per_year = yearly_data[self.crime_columns].sum(axis=1)
        avg_crime_rate = total_crime_per_year.mean()

        # Categorize
        if avg_crime_rate < 100:
            crime_label, color = "SAFEST", "deepskyblue"
        elif avg_crime_rate < 300:
            crime_label, color = "SAFE", "green"
        elif avg_crime_rate < 600:
            crime_label, color = "MODERATE", "gold"
        elif avg_crime_rate < 1000:
            crime_label, color = "DANGER", "orange"
        else:
            crime_label, color = "DANGEROUS", "red"
    
        # Return the results
        return {
            'location': location.title(),
            'type': location_type,
            'yearly_data': yearly_data,
            'pct_change': pct_change.fillna(0).to_dict('records'),
            'crime_columns': self.crime_columns,
            'risk_level': crime_label,
            'risk_color': color
        }

    def create_visualizations(self, analysis_data):
        """Generate Plotly figures"""
        figs = {}
        
        # 1. Yearly trends plot
        figs['trend'] = self._create_trend_plot(analysis_data)
        
        # 2. Crime composition plot
        figs['composition'] = self._create_composition_plot(analysis_data)
        
        # 3. District comparison (if available)
        if analysis_data['district_comparison'] is not None:
            figs['districts'] = self._create_district_plot(analysis_data)
            
        return figs

    
    def create_crime_trends_plot(self, analysis_data):
        """Create trend visualization with optimized subplots"""
    
        # Debugging: Print the structure of analysis_data
        print("Analysis Data:", analysis_data)
    
        # Ensure 'crime_columns' is a list
        if isinstance(analysis_data, dict):
            if 'crime_columns' in analysis_data:
                crime_columns = analysis_data['crime_columns']
                print(f"Crime Columns: {crime_columns}")
            else:
                raise ValueError("No 'crime_columns' found in analysis_data")
        else:
            raise ValueError("Expected 'analysis_data' to be a dictionary")

        # Check if 'crime_columns' is indeed a list
        if not isinstance(crime_columns, list):
            raise ValueError(f"Expected 'crime_columns' to be a list, but got {type(crime_columns)}")

        # Check if 'crime_columns' is empty
        if not crime_columns:
            raise ValueError("The 'crime_columns' list is empty.")
    
        # Get the number of rows and columns based on crime_columns
        cols = 5  # You can adjust this based on the total number of columns
        rows = (len(crime_columns) // cols) + (1 if len(crime_columns) % cols != 0 else 0)

        # Create subplots with reduced rows and multiple columns
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=crime_columns,
            vertical_spacing=0.05,
            shared_xaxes=True,
        )

        # Ensure 'yearly_data' is present and has data
        yearly_data = analysis_data.get('yearly_data', None)
        if yearly_data is None:
             raise ValueError("Yearly data is missing or None in analysis_data")

        # Add the traces for each crime column
        for i, crime in enumerate(crime_columns):
            row = (i // cols) + 1
            col = (i % cols) + 1

            # Plot each crime column in a separate subplot
            if crime in yearly_data.columns:
                fig.add_trace(
                    go.Bar(
                        x=yearly_data['YEAR'],
                        y=yearly_data[crime],
                        name=crime,
                        marker_color=px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
                    ),
                    row=row, col=col
                )

        # Update layout for better visualization
        fig.update_layout(
            height=300 * rows,
            title_text=f"Crime Trends in {analysis_data['location']} (2001-2012)",
            showlegend=False,
            title_x=0.5,
        )

        return fig
    
    def _create_composition_plot(self, analysis_data):
        """Create pie chart of crime composition"""
        return px.pie(
            names=analysis_data['crime_composition'].index,
            values=analysis_data['crime_composition'].values,
            title=f'Crime Composition in {analysis_data["latest_year"]}'
        )
    
    def _create_district_plot(self, analysis_data):
        """Create district comparison plot"""
        return px.bar(
            analysis_data['district_comparison'].reset_index().melt(id_vars='DISTRICT'),
            x='DISTRICT',
            y='value',
            color='variable',
            title=f'District-wise Crime Comparison in {analysis_data["location"]}'
        )