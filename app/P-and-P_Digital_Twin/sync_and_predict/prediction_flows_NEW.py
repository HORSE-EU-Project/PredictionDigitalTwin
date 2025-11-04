import pandas as pd
import configparser
import os
from datetime import datetime
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np

# === CONFIGURAZIONE ===
config = configparser.ConfigParser()
config.read('config.ini')

interval = int(config['FLOW']['interval'])
predicted_sec = int(config['ARIMA']['predicted_sec'])
t = datetime.now().strftime('%H_%M_%S')

flow_file = config['CSV_FLOWS']['detailed_file']
output_dir = "output_HoltWinters"
os.makedirs(output_dir, exist_ok=True)
output_graph_dir = os.path.join(output_dir, "graphs")
os.makedirs(output_graph_dir, exist_ok=True)

print("Uploading CSV:", flow_file)
df = pd.read_csv(flow_file, parse_dates=['timestamp'])
df = df.rename(columns={'timestamp': 'ds', 'throughput': 'y'})

all_predictions = []
combined_all = []

grouped = df.groupby(['ipsrc', 'ipdst'])
for (src, dst), group in grouped:
    group = group.sort_values('ds')
    if group['ds'].nunique() < 10 or len(group) < 20:
        continue

    total_len = len(group)
    train_size = int(total_len * 0.7)
    train = group.iloc[:train_size]
    test = group.iloc[train_size:]

    scaler = MinMaxScaler()
    train_scaled = scaler.fit_transform(train[['y']])
    test_scaled = scaler.transform(test[['y']])

    train_series = pd.Series(train_scaled.flatten(), index=train['ds'])

    try:
        model = ExponentialSmoothing(train_series, trend='add', seasonal=None)
        model_fit = model.fit()

        additional_steps = int(predicted_sec / interval)
        total_forecast_len = len(test) + additional_steps
        forecast = model_fit.forecast(total_forecast_len)

        forecast_rescaled = scaler.inverse_transform(forecast.values.reshape(-1, 1))
        forecast_rescaled[forecast_rescaled < 0] = 0

        forecast_index = pd.date_range(start=train['ds'].iloc[-1] + pd.Timedelta(seconds=interval),
                                       periods=len(forecast), freq=f'{interval}S')

        df_pred = pd.DataFrame({
            'ds': forecast_index,
            'y': forecast_rescaled.flatten(),
            'ipsrc': src,
            'ipdst': dst
        })

        all_predictions.append(df_pred)

        df_test_combined = pd.concat([group.iloc[train_size:], df_pred.iloc[len(test):]], ignore_index=True)
        combined_all.append(df_test_combined)

        # === GRAFICO ===
        plt.figure(figsize=(12, 6))
        plt.plot(group['ds'], group['y'], label='Originale', color='blue')
        plt.plot(df_pred['ds'], df_pred['y'], label='Predizione', color='red')
        plt.title(f'Flusso {src} → {dst}')
        plt.xlabel('Tempo')
        plt.ylabel('Throughput (bit/s)')
        plt.legend()
        plt.tight_layout()

        graph_file = os.path.join(output_graph_dir, f'pred_{src.replace(".", "_")}_{dst.replace(".", "_")}_{t}.png')
        plt.savefig(graph_file)
        plt.close()

        print(f"Predizione completata per {src} → {dst}, grafico salvato: {graph_file}")

    except Exception as e:
        print(f"Errore nel flusso {src} → {dst}: {e}")

# === OUTPUT ===
if all_predictions:
    final_df = pd.concat(all_predictions)
    combined_df = pd.concat(combined_all)

    final_output_file = os.path.join(output_dir, f'predicted_flows_{t}.csv')
    combined_output_file = os.path.join(output_dir, f'final_combined_prediction_{t}.csv')

    final_df.to_csv(final_output_file, index=False)
    combined_df.to_csv(combined_output_file, index=False)

    if 'OUTPUT_ARIMA' not in config:
        config.add_section('OUTPUT_ARIMA')
    config['OUTPUT_ARIMA']['predicted_csv'] = combined_output_file

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    print(f"\nTutte le predizioni salvate in: {final_output_file}")
    print(f"\nFile compatibile con sistema originale: {combined_output_file}")
else:
    print("\nNessuna predizione generata: troppi pochi dati per ogni flusso.")
