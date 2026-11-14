"""
Crime Analysis Engine for KnowYourLocality
-----------------------------------------
Author: KnowYourLocality
Source Authority: National Crime Records Bureau (NCRB), Ministry of Home Affairs, Government of India
Census Benchmark: Census of India 2011 (Registrar General & Census Commissioner)
"""

import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fetch_government_data import get_population_for_location

# Broad category groupings for clear consumer understanding
CRIME_DOMAINS = {
    'Violent Crimes': [
        'MURDER', 'ATTEMPT TO MURDER', 'A. MURDER', 'CULPABLE HOMICIDE',
        'RIOTS', 'ARSON', 'HURT/GREVIOUS HURT'
    ],
    "Women's Safety": [
        'RAPE', 'CUSTODIAL RAPE', 'OTHER RAPE', 'KIDNAPPING OF WOMEN',
        'DOWRY DEATHS', 'ASSAULT ON WOMEN WITH INTENT TO OUTRAGE HER MODESTY',
        'INSULT TO MODESTY OF WOMEN', 'CRUELTY BY IN-LAWS', 'IMPORTATION OF GIRLS'
    ],
    'Property & Theft': [
        'BURGLARY', 'THEFT', 'AUTO THEFT', 'OTHER THEFT', 'ROBBERY',
        'DACOITY', 'PREPARATION FOR DACOITY'
    ],
    'Other IPC & Economic': [
        'CRIMINAL BREACH OF TRUST', 'CHEATING', 'COUNTERFIETING',
        'DEATH BY NEGLIGENCE', 'OTHER IPC CRIMES'
    ]
}

# National baseline crime rate per 100k citizens from NCRB reports
NCRB_NATIONAL_AVG_CRIME_RATE = 215.0

# Centroid coordinates for all 35 States & Union Territories of India
STATE_COORDINATES = {
    "A & N ISLANDS": {"name": "Andaman & Nicobar Islands", "lat": 11.7401, "lng": 92.6586},
    "ANDHRA PRADESH": {"name": "Andhra Pradesh", "lat": 15.9129, "lng": 79.7400},
    "ARUNACHAL PRADESH": {"name": "Arunachal Pradesh", "lat": 28.2180, "lng": 94.7278},
    "ASSAM": {"name": "Assam", "lat": 26.2006, "lng": 92.9376},
    "BIHAR": {"name": "Bihar", "lat": 25.0961, "lng": 85.3131},
    "CHANDIGARH": {"name": "Chandigarh", "lat": 30.7333, "lng": 76.7794},
    "CHHATTISGARH": {"name": "Chhattisgarh", "lat": 21.2787, "lng": 81.8661},
    "D & N HAVELI AND DAMAN & DIU": {"name": "Dadra & Nagar Haveli and Daman & Diu", "lat": 20.4283, "lng": 72.8397},
    "DELHI UT": {"name": "Delhi", "lat": 28.7041, "lng": 77.1025},
    "GOA": {"name": "Goa", "lat": 15.2993, "lng": 74.1240},
    "GUJARAT": {"name": "Gujarat", "lat": 22.2587, "lng": 71.1924},
    "HARYANA": {"name": "Haryana", "lat": 29.0588, "lng": 76.0856},
    "HIMACHAL PRADESH": {"name": "Himachal Pradesh", "lat": 31.1048, "lng": 77.1734},
    "JAMMU & KASHMIR": {"name": "Jammu & Kashmir", "lat": 33.7782, "lng": 76.5762},
    "JHARKHAND": {"name": "Jharkhand", "lat": 23.6102, "lng": 85.2799},
    "KARNATAKA": {"name": "Karnataka", "lat": 15.3173, "lng": 75.7139},
    "KERALA": {"name": "Kerala", "lat": 10.8505, "lng": 76.2711},
    "LAKSHADWEEP": {"name": "Lakshadweep", "lat": 10.5667, "lng": 72.6417},
    "MADHYA PRADESH": {"name": "Madhya Pradesh", "lat": 22.9734, "lng": 78.6569},
    "MAHARASHTRA": {"name": "Maharashtra", "lat": 19.7515, "lng": 75.7139},
    "MANIPUR": {"name": "Manipur", "lat": 24.6637, "lng": 93.9063},
    "MEGHALAYA": {"name": "Meghalaya", "lat": 25.4670, "lng": 91.3662},
    "MIZORAM": {"name": "Mizoram", "lat": 23.1645, "lng": 92.9376},
    "NAGALAND": {"name": "Nagaland", "lat": 26.1584, "lng": 94.5624},
    "ODISHA": {"name": "Odisha", "lat": 20.9517, "lng": 85.0985},
    "PUDUCHERRY": {"name": "Puducherry", "lat": 11.9416, "lng": 79.8083},
    "PUNJAB": {"name": "Punjab", "lat": 31.1471, "lng": 75.3412},
    "RAJASTHAN": {"name": "Rajasthan", "lat": 27.0238, "lng": 74.2179},
    "SIKKIM": {"name": "Sikkim", "lat": 27.5330, "lng": 88.5122},
    "TAMIL NADU": {"name": "Tamil Nadu", "lat": 11.1271, "lng": 78.6569},
    "TELANGANA": {"name": "Telangana", "lat": 17.8749, "lng": 78.1008},
    "TRIPURA": {"name": "Tripura", "lat": 23.9408, "lng": 91.9882},
    "UTTAR PRADESH": {"name": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462},
    "UTTARAKHAND": {"name": "Uttarakhand", "lat": 30.0668, "lng": 79.0193},
    "WEST BENGAL": {"name": "West Bengal", "lat": 22.9868, "lng": 87.8550}
}

class CrimeAnalyzer:
    def __init__(self, data_path="crime_data_clean.csv"):
        if not os.path.exists(data_path) and os.path.exists("crime_data.csv"):
            data_path = "crime_data.csv"
        
        self.df = pd.read_csv(data_path)
        self._clean_data()
        
        self.crime_columns = [
            col for col in self.df.columns 
            if col not in ['STATE', 'DISTRICT', 'YEAR', 'TOTAL IPC CRIMES', 'IS_AGGREGATE_ROW']
        ]
        self._prepare_melted_data()
        self._state_heatmap_cache = None

    def _clean_data(self):
        """Standardize column names and types without dead code."""
        self.df.columns = self.df.columns.str.strip().str.upper()
        
        if 'STATE' not in self.df.columns or 'DISTRICT' not in self.df.columns or 'YEAR' not in self.df.columns:
            raise ValueError("Dataset missing required columns: STATE, DISTRICT, or YEAR")

        self.df['STATE'] = self.df['STATE'].astype(str).str.strip().str.upper()
        self.df['DISTRICT'] = self.df['DISTRICT'].astype(str).str.strip().str.upper()
        self.df['YEAR'] = pd.to_numeric(self.df['YEAR'], errors='coerce').fillna(0).astype(int)

        if 'IS_AGGREGATE_ROW' not in self.df.columns:
            self.df['IS_AGGREGATE_ROW'] = self.df['DISTRICT'].str.contains('TOTAL', na=False)

        for col in self.df.columns:
            if col not in ['STATE', 'DISTRICT', 'YEAR', 'IS_AGGREGATE_ROW']:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

        if 'TOTAL IPC CRIMES' not in self.df.columns:
            crime_cols = [c for c in self.df.columns if c not in ['STATE', 'DISTRICT', 'YEAR', 'IS_AGGREGATE_ROW']]
            self.df['TOTAL IPC CRIMES'] = self.df[crime_cols].sum(axis=1)

    def _prepare_melted_data(self):
        """Prepare melted dataset for rapid category breakdowns."""
        clean_subset = self.df[~self.df['IS_AGGREGATE_ROW']]
        self.melted_df = clean_subset.melt(
            id_vars=['STATE', 'DISTRICT', 'YEAR'],
            value_vars=self.crime_columns,
            var_name='CRIME_TYPE',
            value_name='CASES'
        )

    def get_location_data(self, location):
        """
        Locates data for a specific state or district.
        Excludes aggregate rows to eliminate double-counting.
        Supports exact matches and city/commissionerate aliases (e.g., Pune -> Pune Commr.).
        """
        location = str(location).strip().upper()
        
        # 1. Exact State
        state_rows = self.df[(self.df['STATE'] == location) & (~self.df['IS_AGGREGATE_ROW'])]
        if not state_rows.empty:
            return {
                'type': 'state',
                'name': location,
                'data': state_rows,
                'state_name': location
            }

        # 2. Fuzzy / Prefix match in State (e.g. "Delhi" -> "DELHI UT")
        state_candidates = [s for s in self.df['STATE'].unique() if s.startswith(location) or location in s]
        if state_candidates:
            chosen_state = state_candidates[0]
            state_rows = self.df[(self.df['STATE'] == chosen_state) & (~self.df['IS_AGGREGATE_ROW'])]
            return {
                'type': 'state',
                'name': chosen_state,
                'data': state_rows,
                'state_name': chosen_state
            }

        # 3. Best-coverage District / Commissionerate match
        #    Prefer COMMR./CITY variants, then pick the one with the most years of data.
        all_districts = self.df[~self.df['IS_AGGREGATE_ROW']]['DISTRICT'].unique()
        dist_candidates = [d for d in all_districts if d.startswith(location) or location in d]
        if dist_candidates:
            preferred = [d for d in dist_candidates if 'COMMR' in d or 'CITY' in d]
            pool = preferred if preferred else dist_candidates
            best_dist = None
            best_years = -1
            for d in pool:
                n_years = self.df[(self.df['DISTRICT'] == d) & (~self.df['IS_AGGREGATE_ROW'])]['YEAR'].nunique()
                if n_years > best_years:
                    best_years = n_years
                    best_dist = d

            district_rows = self.df[(self.df['DISTRICT'] == best_dist) & (~self.df['IS_AGGREGATE_ROW'])]
            state_parent = district_rows['STATE'].iloc[0]
            return {
                'type': 'district',
                'name': best_dist,
                'data': district_rows,
                'state_name': state_parent
            }

        return None

    def generate_crime_analysis(self, location):
        """
        Generates comprehensive crime analytics with Census 2011 population normalization,
        0–100 Safety Score index, and domain breakdowns.
        """
        loc_data = self.get_location_data(location)
        if loc_data is None:
            return None

        location_df = loc_data['data']
        location_type = loc_data['type']
        state_name = loc_data['state_name']
        resolved_name = loc_data['name']

        # Group by year and aggregate (sum across all non-aggregate district rows)
        yearly_data = location_df.groupby('YEAR')[self.crime_columns].sum().reset_index()
        yearly_data['TOTAL IPC CRIMES'] = yearly_data[self.crime_columns].sum(axis=1)

        # Percentage change YoY
        pct_change = yearly_data[['YEAR', 'TOTAL IPC CRIMES'] + self.crime_columns].pct_change() * 100
        pct_change['YEAR'] = yearly_data['YEAR']

        # Census Population Normalization (Fix M1.2)
        population = get_population_for_location(resolved_name, location_type, state_name)
        avg_annual_crimes = yearly_data['TOTAL IPC CRIMES'].mean()
        crime_rate_per_100k = round((avg_annual_crimes / population) * 100000, 2)

        # Phase 2: Compute Composite Safety Score (0–100 Scale)
        # Scaled so national average ~215 lands at ~65/100, low crime <100 lands at 85-95/100
        raw_score = 100 - (crime_rate_per_100k * 0.16)
        safety_score = int(round(np.clip(raw_score, 12, 97)))

        # Domain Breakdowns and Sub-Scores (0-100 each)
        domain_breakdown = {}
        domain_scores = {}
        num_years = max(1, len(yearly_data))

        # Weighting factors to compute domain sub-scores
        domain_factors = {
            'Violent Crimes': 0.85,
            "Women's Safety": 0.70,
            'Property & Theft': 0.45,
            'Other IPC & Economic': 0.35
        }

        for domain, cols in CRIME_DOMAINS.items():
            matching_cols = [c for c in cols if c in yearly_data.columns]
            if matching_cols:
                domain_total = yearly_data[matching_cols].sum().sum()
                domain_breakdown[domain] = int(domain_total)
                
                # Annual domain rate per 100k
                annual_domain_rate = (domain_total / num_years / population) * 100000
                d_factor = domain_factors.get(domain, 0.5)
                sub_score = int(round(np.clip(100 - (annual_domain_rate * d_factor), 15, 98)))
                domain_scores[domain] = sub_score
            else:
                domain_breakdown[domain] = 0
                domain_scores[domain] = 85

        # Benchmark comparison statement
        diff_pct = round(((crime_rate_per_100k - NCRB_NATIONAL_AVG_CRIME_RATE) / NCRB_NATIONAL_AVG_CRIME_RATE) * 100, 1)
        if diff_pct < 0:
            benchmark_text = f"{abs(diff_pct)}% lower incidents than the all-India national average"
            benchmark_class = "text-success"
        else:
            benchmark_text = f"{abs(diff_pct)}% higher reported incidents than national average"
            benchmark_class = "text-danger"

        # Risk Stratification
        if safety_score >= 80:
            risk_label, risk_color = "SAFE / LOW RISK", "#198754"
            safety_badge_class = "bg-success text-white"
        elif safety_score >= 65:
            risk_label, risk_color = "MODERATE SAFETY", "#ffc107"
            safety_badge_class = "bg-warning text-dark"
        elif safety_score >= 45:
            risk_label, risk_color = "ELEVATED CONCERN", "#fd7e14"
            safety_badge_class = "bg-orange text-white"
        else:
            risk_label, risk_color = "HIGH RISK WATCHLIST", "#dc3545"
            safety_badge_class = "bg-danger text-white"

        latest_year = int(yearly_data['YEAR'].max())
        earliest_year = int(yearly_data['YEAR'].min())

        return {
            'location': resolved_name.title(),
            'state_name': state_name.title(),
            'type': location_type,
            'population': population,
            'avg_annual_crimes': int(round(avg_annual_crimes)),
            'crime_rate_per_100k': crime_rate_per_100k,
            'safety_score': safety_score,
            'domain_scores': domain_scores,
            'benchmark_text': benchmark_text,
            'benchmark_class': benchmark_class,
            'risk_level': risk_label,
            'risk_color': risk_color,
            'safety_badge_class': safety_badge_class,
            'yearly_data': yearly_data,
            'pct_change': pct_change.fillna(0).to_dict('records'),
            'domain_breakdown': domain_breakdown,
            'crime_columns': self.crime_columns,
            'period': f"{earliest_year} - {latest_year}"
        }

    def compare_locations(self, loc1_str, loc2_str):
        """
        Phase 2: Generates comparative safety analysis for two localities.
        """
        a1 = self.generate_crime_analysis(loc1_str)
        a2 = self.generate_crime_analysis(loc2_str)

        if not a1 or not a2:
            return None

        # Deltas
        score_diff = a1['safety_score'] - a2['safety_score']
        rate_diff = round(a1['crime_rate_per_100k'] - a2['crime_rate_per_100k'], 2)

        # Plotly comparison figure
        fig = go.Figure()
        y1 = a1['yearly_data']
        y2 = a2['yearly_data']

        fig.add_trace(go.Scatter(
            x=y1['YEAR'],
            y=y1['TOTAL IPC CRIMES'],
            mode='lines+markers',
            name=f"{a1['location']} (Total IPC)",
            line=dict(color='#0d6efd', width=3),
            marker=dict(size=7)
        ))

        fig.add_trace(go.Scatter(
            x=y2['YEAR'],
            y=y2['TOTAL IPC CRIMES'],
            mode='lines+markers',
            name=f"{a2['location']} (Total IPC)",
            line=dict(color='#dc3545', width=3, dash='dash'),
            marker=dict(size=7)
        ))

        fig.update_layout(
            title=f"Incident Trajectory Comparison: {a1['location']} vs {a2['location']}",
            xaxis_title="Year",
            yaxis_title="Total Reported Crimes",
            template="plotly_white",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=80, b=40)
        )

        import json
        return {
            'loc1': a1,
            'loc2': a2,
            'score_diff': score_diff,
            'rate_diff': rate_diff,
            'comparison_chart_json': json.loads(fig.to_json())
        }

    def create_crime_trends_plot(self, analysis_data):
        """
        Creates clean, responsive Plotly visualizations:
        1. High-level Total IPC Crimes trend line.
        2. Top 5 crime heads breakdown.
        """
        yearly_data = analysis_data['yearly_data']
        location_title = analysis_data['location']
        period = analysis_data.get('period', 'Historical')

        crime_totals = yearly_data[self.crime_columns].sum().sort_values(ascending=False)
        top_crimes = crime_totals.head(5).index.tolist()

        fig = go.Figure()

        # Total IPC Crimes
        fig.add_trace(go.Scatter(
            x=yearly_data['YEAR'],
            y=yearly_data['TOTAL IPC CRIMES'],
            mode='lines+markers',
            name='Total IPC Crimes',
            line=dict(color='#0d6efd', width=3),
            marker=dict(size=8)
        ))

        colors = ['#dc3545', '#198754', '#fd7e14', '#6f42c1', '#20c997']
        for i, crime in enumerate(top_crimes):
            fig.add_trace(go.Scatter(
                x=yearly_data['YEAR'],
                y=yearly_data[crime],
                mode='lines+markers',
                name=crime.title(),
                line=dict(dash='dot', color=colors[i % len(colors)]),
                visible='legendonly'  # hidden by default, togglable
            ))

        fig.update_layout(
            title=f"Crime Trends in {location_title} ({period})",
            xaxis_title="Year",
            yaxis_title="Reported Incidents",
            template="plotly_white",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.20,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=40, r=40, t=60, b=100)
        )

        return fig

    def get_state_crime_heatmap_data(self):
        """
        Calculates state-wise average crime rates, census population normalization,
        and heat intensity metrics for interactive heatmap visualization.
        """
        if self._state_heatmap_cache is not None:
            return self._state_heatmap_cache

        state_data = []
        for state_key, meta in STATE_COORDINATES.items():
            analysis = self.generate_crime_analysis(state_key)
            if not analysis:
                continue

            crime_rate = float(analysis['crime_rate_per_100k'])
            avg_annual = int(analysis['avg_annual_crimes'])
            pop = int(analysis['population'])
            safety_score = int(analysis['safety_score'])

            state_data.append({
                'state_key': state_key,
                'name': meta['name'],
                'query': meta['name'],
                'lat': meta['lat'],
                'lng': meta['lng'],
                'crime_rate_per_100k': crime_rate,
                'avg_annual_crimes': avg_annual,
                'population': f"{pop:,}",
                'raw_population': pop,
                'safety_score': safety_score,
                'risk_level': analysis['risk_level'],
                'risk_color': analysis['risk_color']
            })

        if not state_data:
            return {'points': [], 'summary': {}}

        # Calculate national summary metrics
        rates = [item['crime_rate_per_100k'] for item in state_data]
        min_rate = min(rates)
        max_rate = max(rates)
        rate_range = max(1.0, max_rate - min_rate)
        
        total_crimes = sum(item['avg_annual_crimes'] for item in state_data)
        total_pop = sum(item['raw_population'] for item in state_data)
        national_weighted_avg = round((total_crimes / max(1, total_pop)) * 100000, 2)
        arithmetic_avg = round(sum(rates) / len(rates), 2)

        lowest_item = min(state_data, key=lambda x: x['crime_rate_per_100k'])
        highest_item = max(state_data, key=lambda x: x['crime_rate_per_100k'])

        # Calculate heat intensity and heat category for each state
        for item in state_data:
            rate = item['crime_rate_per_100k']
            # Normalized intensity from 0.20 to 1.00 for Leaflet heat layer
            intensity = round(0.20 + 0.80 * ((rate - min_rate) / rate_range), 3)
            item['heat_intensity'] = intensity

            # Heat level classification and color based on average crime rate
            if rate < 160:
                item['heat_level'] = 'Low Heat'
                item['heat_color'] = '#28a745'
                item['heat_badge'] = 'bg-success text-white'
                item['heat_desc'] = 'Low crime incidence relative to national levels'
            elif rate < 260:
                item['heat_level'] = 'Moderate Heat'
                item['heat_color'] = '#f1c40f'
                item['heat_badge'] = 'bg-warning text-dark'
                item['heat_desc'] = 'Moderate crime incidence near national baseline'
            elif rate < 360:
                item['heat_level'] = 'High Heat'
                item['heat_color'] = '#fd7e14'
                item['heat_badge'] = 'bg-orange text-white'
                item['heat_desc'] = 'Elevated crime incidence requiring heightened awareness'
            else:
                item['heat_level'] = 'Severe Heat'
                item['heat_color'] = '#dc3545'
                item['heat_badge'] = 'bg-danger text-white'
                item['heat_desc'] = 'High per-capita crime concentration'

            # Relative comparison with national average
            diff_pct = round(((rate - national_weighted_avg) / national_weighted_avg) * 100, 1)
            if diff_pct < 0:
                item['vs_national_text'] = f"{abs(diff_pct)}% below national avg ({national_weighted_avg})"
                item['vs_national_class'] = 'text-success'
            else:
                item['vs_national_text'] = f"{abs(diff_pct)}% above national avg ({national_weighted_avg})"
                item['vs_national_class'] = 'text-danger'
            item['diff_pct'] = diff_pct

        summary = {
            'total_states': len(state_data),
            'national_weighted_avg': national_weighted_avg,
            'national_arithmetic_avg': arithmetic_avg,
            'min_rate': min_rate,
            'max_rate': max_rate,
            'lowest_state': lowest_item['name'],
            'lowest_state_rate': min_rate,
            'highest_state': highest_item['name'],
            'highest_state_rate': max_rate
        }

        self._state_heatmap_cache = {
            'points': state_data,
            'summary': summary
        }
        return self._state_heatmap_cache

    def generate_csv_data(self, location):
        """
        Phase 3: Exports multi-year historical crime data and calculated rates as CSV string.
        """
        loc_data = self.get_location_data(location)
        if not loc_data:
            return None

        location_df = loc_data['data']
        resolved_name = loc_data['name']
        loc_type = loc_data['type']
        state_name = loc_data['state_name']
        population = get_population_for_location(resolved_name, loc_type, state_name)

        yearly = location_df.groupby('YEAR')[self.crime_columns].sum().reset_index()
        yearly['TOTAL IPC CRIMES'] = yearly[self.crime_columns].sum(axis=1)
        yearly['POPULATION_BENCHMARK'] = population
        yearly['CRIME_RATE_PER_100K'] = ((yearly['TOTAL IPC CRIMES'] / population) * 100000).round(2)
        yearly['SAFETY_SCORE_INDEX'] = yearly['CRIME_RATE_PER_100K'].apply(
            lambda r: int(round(np.clip(100 - (r * 0.16), 12, 97)))
        )
        yearly.insert(0, 'STATE', state_name.title())
        yearly.insert(0, 'LOCATION', resolved_name.title())

        import io
        buf = io.StringIO()
        yearly.to_csv(buf, index=False)
        return buf.getvalue()

    def get_rankings_data(self, state=None, domain=None, sort='safest', limit=100):
        """
        Phase 3: Computes and returns ranked districts across India or within a state.
        Allows filtering by State, Domain (e.g. Women's Safety, Violent Crimes),
        and sorting by Safest vs High-Concern.
        """
        if not hasattr(self, '_rankings_cache'):
            self._rankings_cache = {}

        cache_key = f"{state}_{domain}_{sort}_{limit}"
        if cache_key in self._rankings_cache:
            return self._rankings_cache[cache_key]

        clean_df = self.df[~self.df['IS_AGGREGATE_ROW']]
        
        # Determine target crime columns based on domain
        if domain and domain in CRIME_DOMAINS:
            target_cols = [c for c in CRIME_DOMAINS[domain] if c in self.crime_columns]
        else:
            target_cols = self.crime_columns

        # Filter by state if provided
        if state and state.strip():
            state_clean = state.strip().upper()
            filtered_df = clean_df[clean_df['STATE'] == state_clean]
            if filtered_df.empty:
                matched_states = [s for s in clean_df['STATE'].unique() if state_clean in s]
                if matched_states:
                    filtered_df = clean_df[clean_df['STATE'] == matched_states[0]]
                else:
                    filtered_df = clean_df
        else:
            filtered_df = clean_df

        # Filter out non-geographic police administrative units
        exclude_keywords = [
            'CID', 'RLY', 'RAILWAY', 'RAILWAYS', 'CRIME', 'STF', 'SPECIAL', 'GRP', 'METRO',
            'BIEO', 'TOTAL', 'SQUAD', 'VIGILANCE', 'TASK FORCE', 'CICE', 'ACB', 'EOW',
            'CELL', 'HEADQUARTERS', 'HQ', 'COMMISSIONERATE', 'CYBER CRIME'
        ]

        district_records = []
        grouped = filtered_df.groupby(['STATE', 'DISTRICT'])

        for (st, dist), grp in grouped:
            dist_str = str(dist).upper()
            if any(k in dist_str for k in exclude_keywords):
                continue

            num_years = max(1, grp['YEAR'].nunique())
            if domain and domain in CRIME_DOMAINS:
                total_crimes = grp[target_cols].sum().sum()
            else:
                total_crimes = grp['TOTAL IPC CRIMES'].sum()

            avg_annual_crimes = total_crimes / num_years
            population = get_population_for_location(dist, 'district', st)
            crime_rate = round((avg_annual_crimes / max(1, population)) * 100000, 2)
            safety_score = int(round(np.clip(100 - (crime_rate * 0.16), 12, 97)))

            # Risk Label
            if safety_score >= 80:
                risk_label = "SAFE / LOW RISK"
                risk_color = "#198754"
                badge_class = "bg-success text-white"
            elif safety_score >= 65:
                risk_label = "MODERATE SAFETY"
                risk_color = "#ffc107"
                badge_class = "bg-warning text-dark"
            elif safety_score >= 45:
                risk_label = "ELEVATED CONCERN"
                risk_color = "#fd7e14"
                badge_class = "bg-orange text-white"
            else:
                risk_label = "HIGH RISK WATCHLIST"
                risk_color = "#dc3545"
                badge_class = "bg-danger text-white"

            district_records.append({
                'district': dist.title(),
                'state': st.title(),
                'crime_rate_per_100k': crime_rate,
                'safety_score': safety_score,
                'avg_annual_crimes': int(round(avg_annual_crimes)),
                'population': f"{population:,}",
                'raw_population': population,
                'risk_level': risk_label,
                'risk_color': risk_color,
                'badge_class': badge_class,
                'domain_analyzed': domain if domain else 'All IPC Crimes'
            })

        # Sort districts
        if sort == 'vulnerable':
            district_records.sort(key=lambda x: x['crime_rate_per_100k'], reverse=True)
        else:  # 'safest'
            district_records.sort(key=lambda x: x['crime_rate_per_100k'])

        for idx, rec in enumerate(district_records):
            rec['rank'] = idx + 1

        result = {
            'districts': district_records[:limit],
            'total_districts': len(district_records),
            'current_state': state.title() if state else 'All India',
            'current_domain': domain if domain else 'All IPC Crimes',
            'current_sort': sort,
            'states_available': sorted([s.title() for s in self.df['STATE'].unique() if s]),
            'domains_available': list(CRIME_DOMAINS.keys())
        }

        self._rankings_cache[cache_key] = result
        return result