from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.utils
import json
import os
from io import StringIO

app = Flask(__name__)

# --- DEBUG: Show which templates Flask can see ---
import os
templates_path = os.path.join(os.path.dirname(__file__), 'templates')
print(f"🔍 Looking for templates in: {templates_path}")
if os.path.exists(templates_path):
    files = os.listdir(templates_path)
    print(f"📁 Files found in templates folder: {files}")
else:
    print(f"❌ The 'templates' folder does NOT exist at {templates_path}")
# 3. THE MAIN ROUTE – HOME PAGE (INPUT FORM)
@app.route('/', methods=['GET', 'POST'])
def index():
        if request.method == "GET":
                return render_template('index.html')

        # POST: process form
        # to get the data now from the form or input given by user
        uploaded_file = request.files.get('file')
        pasted_data = request.form.get('data')
        df = None     # initialised data frame to store user data
        if uploaded_file and uploaded_file.filename != '':
                df = pd.read_csv(uploaded_file)
        # If no file was uploaded, check if the user pasted text into the textarea.
        elif pasted_data and pasted_data.strip() != '':
                df = pd.read_csv(StringIO(pasted_data))

        if df is None or df.empty:
                return render_template('index.html', error="Please upload a CSV file or paste valid CSV data.")

        # STEP 2: Get the user's analysis choices from the form
        group_col = request.form.get('group_col', '').strip()
        value_col = request.form.get('value_col', '').strip()
        agg_func = request.form.get('agg_func', 'sum')
        chart_type = request.form.get('chart_type', 'bar')
       

        # STEP 3: Validate that the user provided valid column names
        if group_col not in df.columns:
                return render_template('index.html', error=f"Column '{group_col}' not found in your data.")
        if value_col not in df.columns:
                return render_template('index.html', error=f"Column '{value_col}' not found in your data.")

        # STEP 4: Perform Data Aggregation using Pandas
        aggregated = df.groupby(group_col)[value_col].agg(agg_func).reset_index()
        agg_name = {
                'sum': 'Total',
                'mean': 'Average',
                'count': 'Count',
                'min': 'Minimum',
                'max': 'Maximum',
                'std': 'Std Deviation'
        }.get(agg_func, agg_func.capitalize())
        aggregated.rename(columns={value_col: agg_name}, inplace=True)

        # STEP 5: Generate Interactive Chart using Plotly
        if chart_type == 'bar':
                fig = px.bar(aggregated, x=group_col, y=agg_name, title=f'{agg_name} by {group_col}')
        elif chart_type == 'pie':
                fig = px.pie(aggregated, names=group_col, values=agg_name, title=f'{agg_name} by {group_col}')
        elif chart_type == 'line':
                fig = px.line(aggregated, x=group_col, y=agg_name, title=f'{agg_name} by {group_col}', markers=True)
        elif chart_type == 'scatter':
            try:
                fig = px.scatter(aggregated, x=group_col, y=agg_name, title=f'{agg_name} by {group_col}')
            except Exception:
                aggregated['index'] = range(len(aggregated))
                fig = px.scatter(aggregated, x='index', y=agg_name, text=group_col, title=f'{agg_name} by {group_col} (indexed)')
        else:
            fig = px.bar(aggregated, x=group_col, y=agg_name, title=f'{agg_name} by {group_col}')
            # default to bar chart

        plot_html = fig.to_html(full_html=False)
        print(f"🔍 DEBUG: plot_html is {len(plot_html)} characters long")
        table_html = aggregated.to_html(classes='table', index=False)
        print(f"🔍 DEBUG: Sending plot to template (length: {len(plot_html)})")
        return render_template('results.html', plot=plot_html, table=table_html, group_col=group_col, value_col=value_col, agg_func=agg_func, chart_type=chart_type)
            
#RUN THE APP

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)               