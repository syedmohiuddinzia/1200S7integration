# Install: pip install flask plotly pandas requests
from flask import Flask, render_template_string
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.io as pio
import json

app = Flask(__name__)

# Firebase URL
FIREBASE_URL = "https://rs485-plc-default-rtdb.firebaseio.com/.json"
history_df = pd.DataFrame(columns=["time", "humidity", "temperature"])

def get_firebase_data():
    try:
        response = requests.get(FIREBASE_URL, timeout=5)
        data = response.json()
        now = datetime.now()
        return {"time": now, "humidity": data.get("humidity", 0), "temperature": data.get("temperature", 0)}
    except Exception as e:
        print(f"Error fetching data: {e}")
        if not history_df.empty:
            last_row = history_df.iloc[-1]
            return {"time": datetime.now(), "humidity": last_row["humidity"], "temperature": last_row["temperature"]}
        return {"time": datetime.now(), "humidity": 0, "temperature": 0}

# HTML template with auto-refresh
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Siemens S7-1200 Dashboard</title>
    <meta http-equiv="refresh" content="1">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #2E3D4A 0%, #123354 100%);
            min-height: 100vh;
        }
        .dashboard { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            padding: 25px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px;
            color: #333;
        }
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        .current-values {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
        }
        .value-card {
            background: linear-gradient(135deg, #2E3D4A 0%, #123354 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            min-width: 200px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);

            display: flex;                 /* make row layout */
            align-items: center;           /* vertical alignment */
            justify-content: space-between;/* space between text and icon */
        }
        .value-text {
            display: flex;
            flex-direction: column; /* stack number and label */
            text-align: left;       /* align text left */
        }
        .value-number {
            font-size: 1.6em;
            font-weight: bold;
        }
        .value-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .value-card i {
            font-size: 2em;
            margin-left: 15px;
            opacity: 0.9;
        }
        .chart-container {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            height: 500px;
        }
        .stats-container {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .stats-table {
            flex: 1;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
        }
        .stats-table h3 {
            text-align: center;
            margin-top: 0;
            color: #2c3e50;
        }
        .stats-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .stats-table th, .stats-table td {
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid #ddd;
        }
        .stats-table th {
            background-color: #667eea;
            color: white;
        }
        .stats-table tr:hover {
            background-color: #f5f5f5;
        }
        .humidity-table th {
            background-color: #2E3D4A
        }
        .temperature-table th {
            background-color: #2E3D4A;
        }
        .history-table {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .history-table table {
            width: 100%;
            border-collapse: collapse;
        }
        .history-table th, .history-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .history-table th {
            background-color: #2E3D4A;
            color: white;
        }
        .history-table tr:hover {
            background-color: #f5f5f5;
        }
        .time {
            text-align: center; 
            color: #666; 
            font-size: 14px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1><i class="fas fa-industry"></i> Siemens S7-1200, TIA Portal Live Dashboard</h1>
        </div>
        
        <div class="current-values">
        <div class="value-card">
            <div class="value-text">
                <div class="value-number">{{ "%.1f"|format(humidity/10) }}%</div>
                <div class="value-label">Current Humidity</div>
            </div>
            <i class="fas fa-tint"></i>
        </div>

        <div class="value-card">
            <div class="value-text">
                <div class="value-number">{{ "%.1f"|format(temperature/10) }}°C</div>
                <div class="value-label">Current Temperature</div>
            </div>
            <i class="fas fa-thermometer-half"></i>
        </div>
        </div>

        
        <div class="chart-container" id="line-chart"></div>
        
        <div class="stats-container">
            <div class="stats-table humidity-table">
                <h3><i class="fas fa-tint"></i> Humidity Statistics</h3>
                <table>
                    <tr>
                        <th>Statistic</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Minimum</td>
                        <td>{{ "%.1f"|format(humidity_min/10) }}%</td>
                    </tr>
                    <tr>
                        <td>Maximum</td>
                        <td>{{ "%.1f"|format(humidity_max/10) }}%</td>
                    </tr>
                    <tr>
                        <td>Average</td>
                        <td>{{ "%.1f"|format(humidity_avg/10) }}%</td>
                    </tr>
                    <tr>
                        <td>Current</td>
                        <td>{{ "%.1f"|format(humidity/10) }}%</td>
                    </tr>
                </table>
            </div>
            
            <div class="stats-table temperature-table">
                <h3><i class="fas fa-thermometer-half"></i> Temperature Statistics</h3>
                <table>
                    <tr>
                        <th>Statistic</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Minimum</td>
                        <td>{{ "%.1f"|format(temp_min/10) }}°C</td>
                    </tr>
                    <tr>
                        <td>Maximum</td>
                        <td>{{ "%.1f"|format(temp_max/10) }}°C</td>
                    </tr>
                    <tr>
                        <td>Average</td>
                        <td>{{ "%.1f"|format(temp_avg/10) }}°C</td>
                    </tr>
                    <tr>
                        <td>Current</td>
                        <td>{{ "%.1f"|format(temperature/10) }}°C</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="history-table">
            <h3><i class="fas fa-history"></i> Historical Data (Last 10 readings)</h3>
            <table>
                <tr>
                    <th>Time</th>
                    <th>Humidity</th>
                    <th>Temperature</th>
                </tr>
                {% for index, row in history_df.iterrows() %}
                <tr>
                    <td>{{ row.time.strftime('%H:%M:%S') }}</td>
                    <td>{{ "%.1f"|format(row.humidity/10) }}%</td>
                    <td>{{ "%.1f"|format(row.temperature/10) }}°C</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="time">
            <i class="fas fa-sync-alt"></i> Last updated: {{ current_time }} | Auto-refresh every 5 seconds
        </div>
    </div>

    <script>
        // Data from Flask
        const historyData = {{ history_data|tojson }};
        
        // Create line chart with full width
        Plotly.newPlot('line-chart', [{
            x: historyData.time,
            y: historyData.humidity,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Humidity',
            line: {color: '005884', width: 2, dash:'dash'},
            marker: {size: 3, color: '005884'}
        }, {
            x: historyData.time,
            y: historyData.temperature,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Temperature',
            line: {color: '840000', width: 2, dash:'dashdot'},
            marker: {size: 3, color: '840000'}
        }], {
            xaxis: {title: 'Time', tickangle: -45},
            yaxis: {title: 'Value'},
            height: 450,
            showlegend: true,
            legend: {x: 0, y: 1.1, orientation: 'h'},
            margin: {l: 60, r: 30, t: 60, b: 60},
            plot_bgcolor: '#f8f9fa',
            paper_bgcolor: '#f8f9fa'
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    global history_df
    new_data = get_firebase_data()
    history_df = pd.concat([history_df, pd.DataFrame([new_data])], ignore_index=True)
    history_df = history_df.tail(50)  # Keep more data for the plot
    
    # Calculate statistics
    humidity_min = history_df["humidity"].min() if not history_df.empty else 0
    humidity_max = history_df["humidity"].max() if not history_df.empty else 0
    humidity_avg = history_df["humidity"].mean() if not history_df.empty else 0
    temp_min = history_df["temperature"].min() if not history_df.empty else 0
    temp_max = history_df["temperature"].max() if not history_df.empty else 0
    temp_avg = history_df["temperature"].mean() if not history_df.empty else 0
    
    # Prepare data for JavaScript
    history_data = {
        "time": history_df["time"].dt.strftime('%H:%M:%S').tolist(),
        "humidity": (history_df["humidity"]/10).tolist(),
        "temperature": (history_df["temperature"]/10).tolist()
    }
    
    # Get last 10 entries for the table
    table_data = history_df.tail(10)
    
    return render_template_string(html_template, 
                                 humidity=new_data["humidity"],
                                 temperature=new_data["temperature"],
                                 humidity_min=humidity_min,
                                 humidity_max=humidity_max,
                                 humidity_avg=humidity_avg,
                                 temp_min=temp_min,
                                 temp_max=temp_max,
                                 temp_avg=temp_avg,
                                 history_df=table_data.iloc[::-1],  # Reverse to show latest first
                                 history_data=history_data,
                                 current_time=datetime.now().strftime("%H:%M:%S"))

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')