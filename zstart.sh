#!/usr/bin/env bash
clear
./restore_dbs.sh 
./zsetup_terminal_env.sh
echo "✅ Environment loaded"

# wait til containers are healthy
sleep 20

python client.py
echo "✅ Client script executed successfully"




