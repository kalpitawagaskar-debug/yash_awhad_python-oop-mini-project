# EV Battery Thermal Intelligence Dashboard (Streamlit + Plotly)

A Python-based interactive dashboard converted from `EV_Battery_Thermal_Dashboard (1).html` that analyzes thermal runaway risks, temperatures, and degradation across 200,000 real-world EV records using **Python Plotly** and **Streamlit**.

---

## ⚡ Features & Enhancements

1. **3-Stage Battery Charging Splash Screen**:
   - **Stage 1/3 (33%)**: Charges first segment with cyan glow (`#22d3ee`), ingesting vehicle telemetry.
   - **Stage 2/3 (66%)**: Charges second segment with purple glow (`#8b5cf6`), executing data imputation & thermal balancing.
   - **Stage 3/3 (100%)**: Charges third segment with rose-orange glow (`#f97316`), pulsing central lightning bolt before smoothly fading out to reveal the live dashboard.

2. **Clean Header & Polished UI**:
   - Streamlit default Deploy button, toolbar, and decorations are removed.
   - Uniform card heights, balanced margins, and consistent dark glassmorphic containers.

3. **Data Cleaning Pipeline (`ev_battery_failure_dataset (1).csv`)**:
   - Imputes all **533,554 missing values** using **Mode Imputation** (categorical) and **Median Imputation** (numerical).
   - Clamps temperatures $[-30^\circ\text{C}, 90^\circ\text{C}]$ ensuring $\text{Max Temp} \ge \text{Avg Temp}$.
   - Derives `temp_rise` = $\text{Max Cell Temp} - \text{Ambient Temp}$.
   - Cached via `@st.cache_data` for instant multi-filter reactivity.

4. **100% Python Plotly Visualizations**:
   - **Overview**: 6 KPI cards with dataset baseline comparison + Chemistry failure bar chart.
   - **Data Explorer**: Top 8 hottest vehicles table with odometer threshold slider + Group-by aggregations.
   - **Statistics**: Mean, Median, Mode, Variance, Std Dev, IQR + 8-class Grouped frequency table & Plotly bar distribution.
   - **Correlation**: Pearson's $r$ cards + ScatterGL plots against Max Cell Temp.
   - **Regression**: Simple linear regression (Ambient $\to$ Cell Temp) and Multiple linear regression (6 predictors) with MAE, RMSE, and $R^2$ metrics.
   - **Preprocessing**: First 8 normalized values table (Min-Max, Z-score, Decimal scaling) + 4-band discretization chart.
   - **Standard Visualizations**: Line, Bar, Scatter, Donut, Box plot, and Histogram.
   - **Advanced Visualizations**: 2D Pixel heatmaps, Parallel Coordinates (`go.Parcoords`), Star Glyphs (`go.Scatterpolar`), and Treemap (`px.treemap`).

---

## 🚀 How to Run

Double-click `run_dashboard.bat` or run in terminal:

```powershell
python -m streamlit run ev_thermal_dashboard_app.py
```

The app will launch at `http://localhost:8501`.

---

## 🌐 Deployment Options

The project includes pre-configured files for cloud and container deployment:
- **Streamlit Community Cloud (Free)**: Push to GitHub and deploy in 1 click at [share.streamlit.io](https://share.streamlit.io).
- **Hugging Face Spaces (Free • 16GB RAM)**: Ideal for handling the 200,000-row telemetry dataset.
- **Docker / Cloud Run / AWS / Render**: Uses the included `Dockerfile` and `docker-compose.yml`.

For detailed step-by-step instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

