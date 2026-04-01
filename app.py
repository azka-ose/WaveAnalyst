from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from scipy import signal
import io
import json
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

def parse_file(file_storage):
    filename = file_storage.filename.lower()
    content = file_storage.read()

    # Try semicolon CSV (like the sample)
    if filename.endswith('.csv') or filename.endswith('.txt'):
        for sep in [';', ',', '\t', '|']:
            try:
                df = pd.read_csv(io.BytesIO(content), sep=sep, header=0)
                if df.shape[1] >= 2:
                    df.columns = ['datetime', 'value'] + list(df.columns[2:])
                    df['datetime'] = pd.to_datetime(df['datetime'], dayfirst=True)
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    df = df.dropna(subset=['datetime', 'value'])
                    df = df.sort_values('datetime').reset_index(drop=True)
                    return df
            except:
                continue
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        try:
            df = pd.read_excel(io.BytesIO(content), header=0)
            df.columns = ['datetime', 'value'] + list(df.columns[2:])
            df['datetime'] = pd.to_datetime(df['datetime'], dayfirst=True)
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna(subset=['datetime', 'value'])
            df = df.sort_values('datetime').reset_index(drop=True)
            return df
        except Exception as e:
            raise ValueError(f"Cannot read Excel file: {e}")

    raise ValueError("Unsupported file format or cannot parse file.")


def compute_window_samples(df, hours):
    """Estimate samples per N hours based on median time delta."""
    if len(df) < 2:
        return max(1, hours * 60)
    deltas = df['datetime'].diff().dropna()
    median_delta_minutes = deltas.median().total_seconds() / 60
    samples = max(1, round((hours * 60) / median_delta_minutes))
    return samples


def moving_average(series, window):
    return series.rolling(window=window, center=True, min_periods=1).mean()


def time_averaging(df, hours):
    """Resample to hourly bins and return mean."""
    df_indexed = df.set_index('datetime')
    resampled = df_indexed['value'].resample(f'{hours}h').mean().reset_index()
    resampled.columns = ['datetime', 'value']
    return resampled


def low_pass_filter(series, window):
    """Butterworth low-pass filter using cutoff based on window size."""
    n = len(series)
    if n < 10 or window >= n:
        return series.copy()
    clean = series.interpolate().fillna(method='bfill').fillna(method='ffill')
    cutoff = 1.0 / window
    b, a = signal.butter(4, cutoff, btype='low', analog=False)
    filtered = signal.filtfilt(b, a, clean.values)
    return pd.Series(filtered, index=series.index)


def downsample_for_chart(times, values, max_points=2000):
    """Downsample to at most max_points for charting performance."""
    n = len(times)
    if n <= max_points:
        return times, values
    step = n // max_points
    idx = list(range(0, n, step))
    return [times[i] for i in idx], [values[i] for i in idx]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        df = parse_file(file)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if len(df) < 10:
        return jsonify({'error': 'File has too few data points (minimum 10)'}), 400

    result = {}

    # Raw data (downsampled)
    times_raw = df['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist()
    values_raw = df['value'].round(3).tolist()
    t_ds, v_ds = downsample_for_chart(times_raw, values_raw)
    result['raw'] = {'times': t_ds, 'values': v_ds}
    result['total_points'] = len(df)
    result['date_range'] = {
        'start': df['datetime'].min().strftime('%d %b %Y %H:%M'),
        'end': df['datetime'].max().strftime('%d %b %Y %H:%M')
    }

    hours_list = [1, 3, 12, 24, 25]

    # Moving Average
    ma_results = {}
    for h in hours_list:
        w = compute_window_samples(df, h)
        ma = moving_average(df['value'], w)
        t_ds2, v_ds2 = downsample_for_chart(times_raw, ma.round(3).tolist())
        ma_results[f'{h}h'] = {'times': t_ds2, 'values': v_ds2, 'window_samples': w}
    result['moving_average'] = ma_results

    # Time Averaging (resampling)
    ta_results = {}
    for h in [1, 3, 12, 24]:
        ta = time_averaging(df, h)
        ta_results[f'{h}h'] = {
            'times': ta['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist(),
            'values': ta['value'].round(3).tolist()
        }
    result['time_averaging'] = ta_results

    # Low Pass Filter
    lpf_results = {}
    for h in hours_list:
        w = compute_window_samples(df, h)
        lpf = low_pass_filter(df['value'], w)
        t_ds3, v_ds3 = downsample_for_chart(times_raw, lpf.round(3).tolist())
        lpf_results[f'{h}h'] = {'times': t_ds3, 'values': v_ds3, 'window_samples': w}
    result['low_pass_filter'] = lpf_results

    return jsonify(result)


@app.route('/export', methods=['POST'])
def export():
    """Export processed results as CSV."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    category = data.get('category')
    period = data.get('period')
    times = data.get('times', [])
    values = data.get('values', [])

    df_out = pd.DataFrame({'datetime': times, 'value': values})
    buf = io.StringIO()
    df_out.to_csv(buf, index=False)
    buf.seek(0)

    return send_file(
        io.BytesIO(buf.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{category}_{period}.csv'
    )


if __name__ == '__main__':
    app.run(debug=True, port=5000)
