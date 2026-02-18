#!/usr/bin/python3

import os
import csv
import configparser
import hashlib
import traceback
from datetime import datetime
import itertools
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from math import sqrt
from sklearn.metrics import mean_squared_error
from matplotlib import pyplot as plt

try:
    from pmdarima import auto_arima
    PMDARIMA_AVAILABLE = True
except Exception:
    PMDARIMA_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA as SM_ARIMA
    SM_AVAILABLE = True
except Exception:
    SM_AVAILABLE = False

cfg = configparser.ConfigParser()
cfg.read('config.ini')

if 'CSV_FLOWS' not in cfg or 'detailed_file' not in cfg['CSV_FLOWS']:
    raise SystemExit("config.ini deve contenere [CSV_FLOWS] detailed_file = <path>")

detailed_file = cfg['CSV_FLOWS']['detailed_file']
if not os.path.exists(detailed_file):
    raise SystemExit(f"File non trovato: {detailed_file}")

interval = int(cfg['FLOW'].get('interval', 5))
predicted_sec = int(cfg['ARIMA'].get('predicted_sec', 0))
output_dir = "output_Arima"
os.makedirs(output_dir, exist_ok=True)
graph_dir = os.path.join(output_dir, "graphs")
os.makedirs(graph_dir, exist_ok=True)

tstamp_run = datetime.now().strftime('%Y%m%d_%H%M%S')

# user options
USE_LOG1P = True            # apply log1p when scale/variance big
LOG1P_THRESHOLD = 1e6       # mean > threshold -> apply log1p
MIN_POINTS = 10

print("Loading", detailed_file)
df = pd.read_csv(detailed_file)

# detect time and value columns
time_col = None
for c in ('timestamp', 'ds', 'time'):
    if c in df.columns:
        time_col = c
        break
if time_col is None:
    raise SystemExit("CSV must contain 'timestamp' or 'ds' or 'time' column")

if 'throughput' in df.columns:
    value_col = 'throughput'
elif 'packet_length' in df.columns:
    value_col = 'packet_length'
elif 'y' in df.columns:
    value_col = 'y'
else:
    raise SystemExit("CSV must contain 'throughput' or 'packet_length' or 'y' column")


if 'src_port' not in df.columns and 'sport' in df.columns:
    df['src_port'] = df['sport']
if 'dst_port' not in df.columns and 'dport' in df.columns:
    df['dst_port'] = df['dport']
if 'src_port' not in df.columns:
    df['src_port'] = pd.NA
if 'dst_port' not in df.columns:
    df['dst_port'] = pd.NA
if 'protocol' not in df.columns:
    df['protocol'] = pd.NA

# timestamps -> datetime
df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
df = df.dropna(subset=[time_col])
df = df.sort_values(time_col).reset_index(drop=True)

# build 5-tuple key
def flow_key_row(r):
    ipsrc = str(r.get('ipsrc','')).strip()
    ipdst = str(r.get('ipdst','')).strip()
    sport = str(r.get('src_port','-')) if pd.notna(r.get('src_port')) else '-'
    dport = str(r.get('dst_port','-')) if pd.notna(r.get('dst_port')) else '-'
    proto = str(r.get('protocol','-')) if pd.notna(r.get('protocol')) else '-'
    return (ipsrc, ipdst, sport, dport, proto)

df['flow_key'] = df.apply(flow_key_row, axis=1)

groups = df.groupby('flow_key')

summary_metrics = []

generated = 0
for idx, (key, sub) in enumerate(groups, start=1):
    try:
        ipsrc, ipdst, sport, dport, proto = key
        proto_clean = ''.join(c for c in proto if c.isalnum() or c in ('_', '-'))
        nome_carino = f"{ipsrc.replace(':','-')}_{sport}_to_{ipdst.replace(':','-')}_{dport}_{proto_clean}"

        h = hashlib.sha1(str(key).encode()).hexdigest()[:8]
        safe_name = f"flow_{idx}_{nome_carino}_{h}"

        # timeseries
        ts = sub[[time_col, value_col]].copy().rename(columns={time_col:'ds', value_col:'y'})
        ts['ds'] = pd.to_datetime(ts['ds'])
        ts = ts.set_index('ds').sort_index()

        # Resample e pulizia dei dati
        rule = f'{interval}S'
        ts_resampled = ts['y'].resample(rule).sum().fillna(0)

        # Filtro: rimuovi outlier molto bassi (es. blackout di rete o errori)
        q1 = ts_resampled.quantile(0.20)  # da 10% a 20%
        ts_filtered = ts_resampled[ts_resampled > q1]
        ts_filtered = ts_filtered.fillna(method='ffill')

        if len(ts_resampled) < MIN_POINTS:
            print(f"[SKIP] {safe_name}: too few points ({len(ts_resampled)})")
            continue

        # choose whether to log-transform
        use_log = False
        if USE_LOG1P:
            meanv = ts_filtered.mean()
            stdv = ts_filtered.std()
            if meanv >= LOG1P_THRESHOLD or (stdv and meanv/stdv < 0.5 and meanv > 0) or ts_resampled.max() / (ts_resampled.median()+1) > 10:
                use_log = True

        series_for_model = ts_filtered.copy()
        if use_log:
            series_for_model = np.log1p(series_for_model)

        # split train/test (60% train)
        total_points = len(series_for_model)
        train_n = int(total_points * 0.6)
        if train_n < MIN_POINTS:
            print(f"[SKIP] {safe_name}: POCHI DATI ({train_n})")
            continue

        train = series_for_model.iloc[:train_n]
        test = series_for_model.iloc[train_n:]

        print(f"\nProcessing {safe_name}: total={total_points}, train={len(train)}, test={len(test)}, log1p={use_log}")


        selected_order = None
        model_obj = None
        if PMDARIMA_AVAILABLE:
            try:
                model_obj = auto_arima(train, start_p=0, start_q=0,
                                       max_p=5, max_q=5, seasonal=False,
                                       stepwise=True, error_action='ignore',
                                       trace=False, suppress_warnings=True)
                selected_order = (int(model_obj.order[0]), int(model_obj.order[1]), int(model_obj.order[2]))

                # fallback se auto_arima seleziona un modello nullo
                if selected_order == (0,0,0):
                    print(" [WARN] auto_arima ha selezionato (0,0,0) – forzo fallback (2,2,1)")
                    selected_order = (2,2,1)
                else:
                    print(" auto_arima selected:", selected_order)

            except Exception as e:
                print("[WARN] auto_arima failed:", e)
                selected_order = (2,2,1)  # fallback default

        if selected_order is None:
            selected_order = (0,1,1)

        history = list(train.values)
        preds_transformed = []
        for t_i in range(len(test)):
            try:
                # fit a small ARIMA each step (more robust than static mean)
                if SM_AVAILABLE:
                    m = SM_ARIMA(history, order=selected_order)
                    m_fit = m.fit()
                    yhat = m_fit.forecast(steps=1)[0]
                else:
                    if model_obj is not None:
                        yhat = model_obj.predict(n_periods=1)[0]
                    else:
                        yhat = history[-1]
            except Exception:
                yhat = history[-1]
            preds_transformed.append(yhat)
            history.append(test.values[t_i])

        if use_log:
            preds_test = np.expm1(np.array(preds_transformed, dtype=float))
            test_actual = np.expm1(test.values)
        else:
            preds_test = np.array(preds_transformed, dtype=float)
            test_actual = test.values
        try:
            rmse_test = sqrt(mean_squared_error(test_actual, preds_test))
        except Exception:
            rmse_test = None

        full_trans = np.concatenate([train.values, test.values])
        extra_steps = int(predicted_sec // interval) if interval > 0 else 0
        steps_total = extra_steps
        extra_forecast_vals = np.array([], dtype=float)
        extra_conf = None

        if steps_total > 0:
            try:
                if PMDARIMA_AVAILABLE:
                    model_full = auto_arima(full_trans, start_p=0, start_q=0, max_p=5, max_q=5,
                                            seasonal=False, stepwise=True, error_action='ignore',
                                            suppress_warnings=True)
                    fc, conf = model_full.predict(n_periods=steps_total, return_conf_int=True)
                    if use_log:
                        fc_inv = np.expm1(fc)
                        conf_inv = np.expm1(conf)
                    else:
                        fc_inv = fc
                        conf_inv = conf
                    extra_forecast_vals = np.array(fc_inv, dtype=float)
                    extra_conf = conf_inv
                else:
                    if SM_AVAILABLE:
                        m_full = SM_ARIMA(full_trans, order=selected_order)
                        mfull_fit = m_full.fit()
                        pres = mfull_fit.get_forecast(steps=steps_total)
                        fc = pres.predicted_mean
                        ci = pres.conf_int()
                        if use_log:
                            fc_inv = np.expm1(fc)
                            ci_inv = np.expm1(ci.values)
                        else:
                            fc_inv = np.array(fc, dtype=float)
                            ci_inv = ci.values
                        extra_forecast_vals = np.array(fc_inv, dtype=float)
                        extra_conf = ci_inv
            except Exception as e:
                print(f"[WARN] extra forecast failed for {safe_name}: {e}")
                extra_forecast_vals = np.array([], dtype=float)
                extra_conf = None

        test_index = test.index
        future_index = pd.date_range(start=test_index[0], periods=len(preds_test) + len(extra_forecast_vals), freq=f'{interval}S')

        preds_full = np.concatenate([preds_test, extra_forecast_vals]) if len(extra_forecast_vals)>0 else preds_test

        df_pred = pd.DataFrame({
            'ds': future_index[:len(preds_full)],
            'y': preds_full
        })
        df_pred['ipsrc'] = ipsrc
        df_pred['ipdst'] = ipdst
        df_pred['src_port'] = sport
        df_pred['dst_port'] = dport
        df_pred['protocol'] = proto

        out_csv = os.path.join(output_dir, f'pred_{safe_name}_{tstamp_run}.csv')
        df_pred.to_csv(out_csv, index=False)
        print(f"Saved predictions CSV: {out_csv}")

        plt.figure(figsize=(12,6))

        plt.plot(ts_filtered.index, ts_filtered.values, label='Originale', color='blue', alpha=0.6)

        plt.axvline(test.index[0], color='k', linestyle='--', linewidth=0.8)

        plt.plot(df_pred['ds'], df_pred['y'], label='Predizione (test+extra)', color='red')

        title_rmse = f" RMSE_test={rmse_test:.1f}" if rmse_test is not None else ""
        plt.title(f"Flusso {ipsrc} → {ipdst} ({proto}){title_rmse}")
        plt.xlabel('Tempo')
        plt.ylabel(value_col)
        plt.legend()
        plt.tight_layout()
        graph_file = os.path.join(graph_dir, f'pred_{safe_name}_{tstamp_run}.png')
        plt.savefig(graph_file)
        plt.close()
        print(f"Saved plot: {graph_file}")
        summary_metrics.append({ 'flow': safe_name, 'ipsrc': ipsrc, 'ipdst': ipdst, 'proto': proto, 'use_log1p': use_log, 'rmse_test': rmse_test, 'pred_csv': out_csv, 'plot': graph_file })
        generated += 1

    except Exception as e:
        print(f"[ERROR] flow {key}: {e}")
        print(traceback.format_exc())
        continue
if generated > 0:
    last_csv_path = summary_metrics[-1]['pred_csv']
    if 'OUTPUT_ARIMA' not in cfg:
        cfg.add_section('OUTPUT_ARIMA')
    cfg['OUTPUT_ARIMA']['prediction_csv'] = last_csv_path
    with open('config.ini', 'w', encoding='utf-8') as cf:
        cfg.write(cf)
    print(f"\nSaved prediction_csv to config.ini: {last_csv_path}")
else:
    print("No predictions generated.")

print("Done.")