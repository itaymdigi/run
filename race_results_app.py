import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from collections import defaultdict
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import statistics
from plotly.subplots import make_subplots
import platform
import os

# Set page config with dark theme
st.set_page_config(
    page_title="Race Results Analyzer",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with improved styling and contrast
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
        color: #FFFFFF;
    }
    
    /* Metric styling */
    .stMetric {
        background-color: rgba(0, 0, 0, 0.5) !important;
        padding: 1.5rem !important;
        border-radius: 0.5rem !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    /* Metric label styling */
    .stMetric label {
        color: #00ff00 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 0 10px rgba(0,255,0,0.3) !important;
    }
    
    /* Metric value styling */
    .stMetric [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        font-weight: bold !important;
        text-shadow: 0 0 10px rgba(255,255,255,0.5) !important;
    }
    
    /* Metric delta styling */
    .stMetric [data-testid="stMetricDelta"] {
        color: #00ffff !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        margin-top: 0.3rem !important;
    }
    
    /* Headers and text */
    h1 {
        color: #00ff00 !important;
        font-size: 2.5rem !important;
        font-weight: bold !important;
        text-shadow: 0 0 15px rgba(0,255,0,0.3) !important;
    }
    
    h2, h3 {
        color: #00ffff !important;
        font-weight: bold !important;
        text-shadow: 0 0 10px rgba(0,255,255,0.3) !important;
    }
    
    h4, h5, h6 {
        color: #ff9900 !important;
        font-weight: bold !important;
    }
    
    p, label {
        color: #ffffff !important;
        font-size: 1.1rem !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid rgba(0, 255, 0, 0.3) !important;
        color: #00ff00 !important;
        font-weight: 500 !important;
    }
    
    .stSelectbox label {
        color: #00ff00 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    
    /* Warning messages with improved visibility */
    .stAlert {
        background-color: rgba(255, 193, 7, 0.2) !important;
        color: #ffd700 !important;
        border: 1px solid rgba(255, 193, 7, 0.5) !important;
        padding: 1rem !important;
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
    }
    
    /* File uploader styling */
    .stFileUploader {
        background-color: rgba(0, 0, 0, 0.5) !important;
        border: 2px dashed #00ff00 !important;
        padding: 1rem !important;
        border-radius: 0.5rem !important;
    }
    
    /* Table styling */
    .stDataFrame {
        background-color: rgba(0, 0, 0, 0.5) !important;
    }
    
    .dataframe {
        color: #ffffff !important;
        font-size: 1rem !important;
    }
    
    /* Dark theme overrides */
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117 !important;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(0, 0, 0, 0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

def parse_time(time_str):
    try:
        if ':' in time_str:
            if '.' in time_str:  # Format: MM:SS.ms
                return sum(float(x) * 60 ** i for i, x in enumerate(reversed(time_str.split(':'))))
            else:  # Format: HH:MM or MM:SS
                parts = time_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:  # MM:SS
                    return int(parts[0]) * 60 + int(parts[1])
        return float(time_str)
    except:
        return float('inf')

def analyze_results(results, distance):
    if not results:
        return None
    
    try:
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        
        # Filter by distance and create a copy
        df_distance = df[df['מקצה'] == distance].copy()
        
        if df_distance.empty:
            return None

        # Convert times to seconds for analysis
        df_distance['time_seconds'] = df_distance['תוצאה'].apply(parse_time)
        
        # Sort by time for consistent results
        df_distance = df_distance.sort_values('time_seconds')
        
        # Find best result (minimum time)
        best_result = df_distance.iloc[0] if not df_distance.empty else None
        
        if best_result is None:
            return None
            
        analysis = {
            'total_races': len(df_distance),
            'best_time': best_result['תוצאה'],
            'best_pace': best_result['קצב'],
            'best_position': best_result['כללי'],
            'avg_pace': df_distance['קצב'].mode().iloc[0] if not df_distance['קצב'].empty else 'N/A',
            'improvement': (df_distance['time_seconds'].iloc[-1] - df_distance['time_seconds'].iloc[0]) 
                          if len(df_distance) > 1 else 0
        }
        
        return analysis, df_distance
    except Exception as e:
        st.error(f"Error analyzing results: {str(e)}")
        return None

def setup_chrome_options():
    """Setup chrome options for both local and cloud deployment"""
    chrome_options = Options()
    
    # Required options for cloud/headless environments
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Memory and process limitations
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-features=NetworkService")
    
    # Resource limitations
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--disk-cache-size=1")
    chrome_options.add_argument("--media-cache-size=1")
    chrome_options.add_argument("--disk-cache-dir=/dev/null")
    chrome_options.add_argument("--window-size=1920x1080")
    
    return chrome_options

def get_chrome_driver():
    """Get Chrome driver based on environment"""
    try:
        chrome_options = setup_chrome_options()
        
        if os.getenv('STREAMLIT_SHARING_MODE') == 'streamlit':
            # We're on Streamlit Cloud - use system chromium-driver
            chrome_service = Service('/usr/bin/chromedriver')
            
            # Set environment variables for Chrome
            os.environ['CHROMIUM_FLAGS'] = '--disable-gpu --no-sandbox --disable-dev-shm-usage'
            
            # Create driver with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
                    return driver
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)  # Wait before retrying
        else:
            # We're running locally - use webdriver_manager
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
                options=chrome_options
            )
            return driver
            
    except Exception as e:
        st.error(f"Error setting up Chrome driver: {str(e)}")
        if os.getenv('STREAMLIT_SHARING_MODE') == 'streamlit':
            st.error("Additional info: Make sure chromium and chromium-driver are installed via packages.txt")
        return None

def scrape_race_results(search_name):
    """Scrape race results with improved error handling"""
    driver = None
    try:
        driver = get_chrome_driver()
        if driver is None:
            return {"error": "Could not initialize Chrome driver"}
        
        # Navigate to the website
        driver.get("https://raceview.net/")
        
        # Wait for search input and interact
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "theQueryText"))
        )
        search_input.clear()
        search_input.send_keys(search_name)
        
        # Click search button
        search_button = driver.find_element(By.ID, "btnSearch")
        search_button.click()
        
        # Wait for results with increased timeout
        time.sleep(3)
        
        # Parse results
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results_table = soup.find('table', class_='resultsTable')
        
        if not results_table:
            return {"error": "No results found"}
        
        # Get headers and results
        headers = [header.text.strip() for header in results_table.find_all('td', class_='resultsTableHeader')]
        
        results = []
        for row in results_table.find_all('tr', class_='resultsTableRow'):
            cells = row.find_all('td')
            result = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    cell_text = cell.find('a').text if cell.find('a') else cell.text
                    result[headers[i]] = cell_text.strip()
            if result:
                results.append(result)
        
        return {
            "headers": headers,
            "results": results
        }
        
    except Exception as e:
        st.error(f"Error scraping results: {str(e)}")
        return {"error": str(e)}
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def calculate_advanced_stats(df_distance):
    """Calculate advanced statistics for the runner's performance"""
    stats = {}
    
    if not df_distance.empty:
        times = df_distance['time_seconds'].tolist()
        stats['median_time'] = statistics.median(times)
        stats['std_dev'] = statistics.stdev(times) if len(times) > 1 else 0
        stats['consistency_score'] = 100 - (stats['std_dev'] / statistics.mean(times) * 100) if len(times) > 1 else 100
        
        # Calculate progression
        if len(times) > 1:
            first_half = times[:len(times)//2]
            second_half = times[len(times)//2:]
            stats['improvement_rate'] = ((statistics.mean(first_half) - statistics.mean(second_half)) / 
                                      statistics.mean(first_half) * 100)
        else:
            stats['improvement_rate'] = 0
            
        # Calculate season bests with proper date parsing
        try:
            # Convert Hebrew date format (DD/MM/YY) to datetime
            df_distance['parsed_date'] = pd.to_datetime(df_distance['תאריך'], format='%d/%m/%y')
            df_distance['year'] = df_distance['parsed_date'].dt.year
            stats['season_bests'] = df_distance.groupby('year')['time_seconds'].min().to_dict()
        except Exception as e:
            # Fallback if date parsing fails
            st.warning(f"Could not parse some dates. Season bests may be incomplete.")
            stats['season_bests'] = {}
        
        # Calculate position improvements
        if 'כללי' in df_distance.columns:
            positions = pd.to_numeric(df_distance['כללי'], errors='coerce')
            stats['best_position'] = positions.min()
            stats['avg_position'] = positions.mean()
            stats['position_improvement'] = positions.iloc[-1] - positions.iloc[0] if len(positions) > 1 else 0
            
    return stats

def create_performance_dashboard(df_distance, stats):
    """Create a comprehensive performance dashboard with multiple charts"""
    
    # Convert dates before creating plots
    try:
        df_distance['parsed_date'] = pd.to_datetime(df_distance['תאריך'], format='%d/%m/%y')
    except Exception as e:
        st.warning("Could not parse some dates. Charts may show dates in original format.")
        df_distance['parsed_date'] = df_distance['תאריך']
    
    # Create subplots with dark theme
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Time Progression', 'Position Progression', 
                       'Time Distribution', 'Pace vs Position'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Update layout for dark theme
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="Performance Analysis Dashboard",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
    )
    
    # Update axes for all subplots
    fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', zerolinecolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', zerolinecolor='rgba(255,255,255,0.1)')
    
    # Add traces with improved visibility
    fig.add_trace(
        go.Scatter(
            x=df_distance['parsed_date'],
            y=df_distance['time_seconds'],
            mode='lines+markers',
            name='Time',
            line=dict(color='#00ff00', width=2),
            marker=dict(size=8)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_distance['parsed_date'],
            y=pd.to_numeric(df_distance['כללי'], errors='coerce'),
            mode='lines+markers',
            name='Position',
            line=dict(color='#ff9900', width=2),
            marker=dict(size=8)
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Histogram(
            x=df_distance['time_seconds'],
            nbinsx=10,
            name='Time Distribution',
            marker_color='#00ffff'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=pd.to_numeric(df_distance['כללי'], errors='coerce'),
            y=df_distance['time_seconds'],
            mode='markers',
            name='Pace vs Position',
            marker=dict(
                size=10,
                color=df_distance['time_seconds'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title=dict(
                        text='Time',
                        side='right',
                        font=dict(color='white')
                    ),
                    tickfont=dict(color='white'),
                    bgcolor='rgba(0,0,0,0)',
                    bordercolor='rgba(255,255,255,0.3)',
                    outlinewidth=1
                )
            )
        ),
        row=2, col=2
    )
    
    # Update subplot titles color
    for annotation in fig.layout.annotations:
        annotation.font.color = 'white'
    
    return fig

def parallel_scrape_results(runner_names):
    """Scrape results for multiple runners in parallel"""
    with ThreadPoolExecutor(max_workers=min(len(runner_names), 4)) as executor:
        future_to_name = {executor.submit(scrape_race_results, name): name for name in runner_names}
        results = {}
        for future in future_to_name:
            name = future_to_name[future]
            try:
                result = future.result()
                if "error" not in result and result.get("results"):
                    results[name] = result["results"]
            except Exception as e:
                st.error(f"Error scraping results for {name}: {str(e)}")
    return results

def format_time(seconds):
    """Format seconds into a readable time string"""
    if seconds == float('inf'):
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02.0f}"
    else:
        return f"{minutes:02d}:{secs:02.0f}"

def format_improvement_rate(rate):
    """Format improvement rate with proper sign and color"""
    if rate > 0:
        return f"↑ {abs(rate):.1f}% Improving"
    else:
        return f"↓ {abs(rate):.1f}% Declining"

def main():
    st.title("🏃 Advanced Race Results Analyzer")
    st.write("Upload a file with runner names or enter names directly for comprehensive race analysis")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload a file with runner names (TXT or CSV)", type=['txt', 'csv'])
    
    with col2:
        manual_input = st.text_input("Or enter a runner's name directly:")
    
    runner_names = []
    
    if uploaded_file:
        try:
            if uploaded_file.type == "text/csv":
                df = pd.read_csv(uploaded_file)
                runner_names = df.iloc[:, 0].tolist()
            else:
                content = uploaded_file.read().decode()
                runner_names = [name.strip() for name in content.split('\n') if name.strip()]
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return
    elif manual_input:
        runner_names = [manual_input]
    
    if runner_names:
        st.write(f"Analyzing results for {len(runner_names)} runner(s)")
        
        with st.spinner('Fetching results for all runners in parallel...'):
            all_results = parallel_scrape_results(runner_names)
        
        if all_results:
            for name, results in all_results.items():
                st.markdown(f"### 📊 Results for {name}")
                
                # Get unique distances
                distances = sorted(list(set(r['מקצה'] for r in results if 'מקצה' in r)))
                
                if not distances:
                    st.warning(f"No race distances found for {name}")
                    continue
                
                # Distance selection with default value
                selected_distance = st.selectbox(
                    f"Select distance for {name}",
                    distances,
                    key=f"distance_{name}"
                )
                
                # Analyze results
                analysis_result = analyze_results(results, selected_distance)
                
                if analysis_result:
                    analysis, df_distance = analysis_result
                    
                    # Calculate advanced statistics
                    advanced_stats = calculate_advanced_stats(df_distance)
                    
                    # Display metrics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🏃 Best Time", format_time(analysis['best_time']))
                    with col2:
                        st.metric("⚡ Best Pace", format_time(analysis['best_pace']))
                    with col3:
                        st.metric("🎯 Total Races", f"{analysis['total_races']}")
                    with col4:
                        consistency = advanced_stats['consistency_score']
                        st.metric("📊 Consistency Score", f"{consistency:.1f}%")
                    
                    # Additional metrics row
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🏆 Best Position", f"#{advanced_stats['best_position']}")
                    with col2:
                        st.metric("📈 Average Position", f"#{advanced_stats['avg_position']:.0f}")
                    with col3:
                        improvement_rate = advanced_stats['improvement_rate']
                        st.metric("💪 Improvement Rate", 
                                f"{abs(improvement_rate):.1f}%",
                                delta=("Improving" if improvement_rate > 0 else "Declining"))
                    with col4:
                        st.metric("📏 Standard Deviation", f"{advanced_stats['std_dev']:.1f}s")
                    
                    # Create and display performance dashboard
                    st.plotly_chart(create_performance_dashboard(df_distance, advanced_stats),
                                  use_container_width=True)
                    
                    # Season Bests Analysis
                    st.markdown("#### 🏆 Season Bests")
                    season_bests = advanced_stats['season_bests']
                    season_df = pd.DataFrame(list(season_bests.items()), 
                                          columns=['Year', 'Best Time'])
                    st.dataframe(season_df, use_container_width=True)
                    
                    # Display detailed results
                    st.markdown("#### 📋 Detailed Results")
                    
                    # Convert to DataFrame for display
                    df_display = pd.DataFrame(df_distance)
                    
                    # Add export buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df_display.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            f"{name}_{selected_distance}_results.csv",
                            "text/csv",
                            key=f'download_csv_{name}'
                        )
                    
                    with col2:
                        excel_buffer = io.BytesIO()
                        df_display.to_excel(excel_buffer, index=False)
                        excel_data = excel_buffer.getvalue()
                        st.download_button(
                            "📊 Download Excel",
                            excel_data,
                            f"{name}_{selected_distance}_results.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f'download_excel_{name}'
                        )
                    
                    # Display table with formatting
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning(f"No results found for {selected_distance}")
        else:
            st.error("No results found for any runner")

if __name__ == "__main__":
    main() 