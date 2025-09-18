#!/usr/bin/python3

import pandas as pd
import configparser
import os
from datetime import datetime
from matplotlib import pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from math import sqrt
import itertools
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from statsmodels.tsa.stattools import acf


config = configparser.ConfigParser()
try:
    config.read('config.ini')
except Exception as error:
    print("\n Couldn't open config.ini: ", error)

output_dir = "output_Arima"
output_graph_dir = "output_Arima/graphs"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(output_graph_dir, exist_ok=True)

interval = int(config['FLOW']['interval'])
predicted_sec = int(config['ARIMA']['predicted_sec'])
t = datetime.now().strftime('%H_%M_%S')

# CSV unico salvato dal parser
flow_file = config['CSV_FLOWS']['detailed_file']


def grid_search_arima(train_scaled, test_scaled, seasonal_lag=None):
    p = d = q = range(0, 2)
    seasonal_pdq = [(x[0], x[1], x[2], seasonal_lag) for x in itertools.product(range(0, 2), repeat=3)]
    
    best_score, best_pdq, best_seasonal_pdq = float("inf"), None, None

    for param in itertools.product(p, d, q):
        try:
            if seasonal_lag:
                for seasonal_param in seasonal_pdq:
                    model = SARIMAX(train_scaled, order=param, seasonal_order=seasonal_param)
                    model_fit = model.fit(method='powell', disp=False)


                    predictions = model_fit.forecast(steps=len(test_scaled))
                    rmse = sqrt(mean_squared_error(test_scaled, predictions))

                    if rmse < best_score:
                        best_score, best_pdq, best_seasonal_pdq = rmse, param, seasonal_param
            else:
                model = ARIMA(train_scaled, order=param)
                model_fit = model.fit(method='powell', disp=False)


                predictions = model_fit.forecast(steps=len(test_scaled))
                rmse = sqrt(mean_squared_error(test_scaled, predictions))

                if rmse < best_score:
                    best_score, best_pdq = rmse, param

        except:
            continue

    return best_score, best_pdq, best_seasonal_pdq if seasonal_lag else None

def detect_seasonality(data, max_lag=50):
    if data.isnull().any():
        return None
    try:
        acf_vals = acf(data, nlags=max_lag)
        significant_lags = [i for i, val in enumerate(acf_vals) if abs(val) > 0.5]
        if significant_lags:
            return significant_lags[0]
    except:
        return None
    return None

print("Uploading CSV:", flow_file)
try:
    df = pd.read_csv(
    flow_file,
    usecols=['ipsrc', 'ipdst', 'timestamp', 'throughput'],
    dtype={'ipsrc': str, 'ipdst': str, 'throughput': float},
    low_memory=False
    )
    df = df.head(20000)
    print("CSV uploaded with ", len(df), "rows")
    print("Finding columns:", df.columns.tolist())
    # Rinomina per adattare allo script
    df = df.rename(columns={'timestamp': 'ds'})
    df['ds'] = pd.to_datetime(df['ds'])
    df = df.dropna(subset=['throughput'])
    
    
    # Usa throughput come colonna target
    if 'throughput' not in df.columns:
        raise ValueError("Il file non contiene la colonna 'throughput'.")
    
    df = df.rename(columns={'throughput': 'y'})
    df = df[['ds', 'ipsrc', 'ipdst', 'y']].dropna()

    total_data = df.shape[0]
    perc_train = int(total_data * 0.7)
    if perc_train >= len(df):
        perc_train = len(df) - 1

    train = df.iloc[:perc_train][['y']]
    test = df.iloc[perc_train:][['y']]

    scaler = MinMaxScaler(feature_range=(0, 1))
    train_scaled = scaler.fit_transform(train[['y']])
    test_scaled = scaler.transform(test[['y']])

    seasonal_lag = detect_seasonality(pd.Series(train['y']))
    print("Ricerca parametri ARIMA/SARIMA...")
    best_rmse, best_pdq, best_seasonal_pdq = grid_search_arima(train_scaled, test_scaled, seasonal_lag)
    print("Parametri migliori trovati:", best_pdq, best_seasonal_pdq)
    if best_pdq is not None:
        p, d, q = best_pdq

        if best_seasonal_pdq:
            model = SARIMAX(train_scaled, order=(p, d, q), seasonal_order=best_seasonal_pdq)
        else:
            model = ARIMA(train_scaled, order=(p, d, q))

        model_fit = model.fit()

        additional_steps = int(predicted_sec / interval)
        start = len(train_scaled)
        end = start + len(test_scaled) + additional_steps - 1

        predictions = model_fit.predict(start=start, end=end)
        predictions_rescaled = scaler.inverse_transform(predictions.reshape(-1, 1))
        predictions_rescaled[predictions_rescaled < 0] = 0

        min_len = min(len(predictions_rescaled), len(test) + additional_steps)

        last_window = df.iloc[-int(len(df) * 0.2):]  # ultimo 20% dati
        ip_pairs = last_window.groupby(['ipsrc', 'ipdst'])['y'].sum().reset_index()
        ip_pairs = ip_pairs.sort_values(by='y', ascending=False)

        if not ip_pairs.empty:
            top_ipsrc, top_ipdst = ip_pairs.iloc[0]['ipsrc'], ip_pairs.iloc[0]['ipdst']
        else:
            top_ipsrc, top_ipdst = None, None

        pred_with_all = pd.DataFrame({
            'ds': pd.date_range(start=df['ds'].iloc[perc_train], periods=min_len, freq=f'{interval}S'),
            'y': predictions_rescaled[:min_len].flatten(),
            'ipsrc': np.append(df['ipsrc'].iloc[perc_train:].values, [top_ipsrc]*additional_steps)[:min_len],
            'ipdst': np.append(df['ipdst'].iloc[perc_train:].values, [top_ipdst]*additional_steps)[:min_len]
        })

        start_prediction_time = pred_with_all['ds'].min()
        df_filtered = df[df['ds'] < start_prediction_time]
        combined = pd.concat([df_filtered, pred_with_all]).sort_values(by='ds').reset_index(drop=True)


        final_output_file = f'{output_dir}/final_combined_prediction_{t}.csv'
        combined.to_csv(final_output_file, index=False)

        if 'CSV_FLOWS' not in config:
            config.add_section('CSV_FLOWS')
        config['CSV_FLOWS']['detailed_file'] = final_output_file


        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        plt.figure(figsize=(15, 8))
        plt.plot(df['ds'], df['y'], label='Dataset originale', color='blue')
        plt.plot(pred_with_all['ds'], pred_with_all['y'], label=f'Predizioni [{p},{d},{q}]', color='red')
        plt.legend(fontsize=12, loc='best')
        plt.xlabel('Timestamp')
        plt.ylabel('Throughput (bit/s)')
        plt.title(f'Predizione throughput con ARIMA [{p},{d},{q}]')
        graph_file = f'{output_graph_dir}/forecast_comparison_{t}.png'
        plt.savefig(graph_file)
        plt.close()

        print(f"Predizione completata. Risultati in: {final_output_file}")
        print(f"Grafico salvato in: {graph_file}")

    else:
        print("Nessuna combinazione di parametri valida trovata per ARIMA/SARIMA.")

except Exception as e:
    print(f"Errore durante l'elaborazione: {e}")
