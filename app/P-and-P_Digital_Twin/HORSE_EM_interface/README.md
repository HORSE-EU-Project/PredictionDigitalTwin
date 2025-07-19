# HORSE SAN P&P NDT Interface with the Early Monitoring module

This directory contains the scripts to interact with the HORSE Early Monitoring module.

## Normal operation

To run the EM interface in background or in a separate terminal:
```
./run_EM_interface.sh
```

To periodically detect new messages from EM:
```
./monitor_EM_input_UPC.sh last.xml
```

Such script file should be edited in order to launch the scripts for predicting the different attacks.

## Testing and DEMO#0

For DEMO#0, please run the following script:
```
./monitor_file_UPC.sh last.xml
```
