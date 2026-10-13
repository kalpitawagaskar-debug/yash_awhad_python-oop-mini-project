@echo off
title EV Battery Thermal Intelligence Dashboard
echo =========================================================================
echo Launching EV Battery Thermal Intelligence Dashboard (Streamlit + Plotly)
echo =========================================================================
echo Folder:  EV_Battery_Thermal_Dashboard_Project
echo Dataset: ev_battery_failure_dataset (1).csv
echo App:     ev_thermal_dashboard_app.py
echo.
python -m streamlit run ev_thermal_dashboard_app.py --server.port 8501 --server.headless false
pause
