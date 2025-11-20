"""
פונקציות עזר משותפות לכל העמודים
"""

import streamlit as st

def load_css():
    """טעינת CSS משותף"""
    st.markdown("""
    <style>
        /* RTL מלא לכל העמוד */
        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* כותרת ראשית */
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #0066CC;
            text-align: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: linear-gradient(135deg, #FFFFFF 0%, #E6F2FF 100%);
            border-radius: 10px;
            border: 2px solid #0066CC;
        }
        
        /* Sidebar RTL */
        [data-testid="stSidebar"] {
            direction: rtl;
            text-align: right;
        }
        
        [data-testid="stSidebar"] > div {
            direction: rtl;
            text-align: right;
        }
        
        /* כפתורים */
        .stButton > button {
            direction: rtl;
            text-align: center;
            background-color: #0066CC;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #0052A3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 102, 204, 0.3);
        }
        
        /* Inputs RTL */
        input, select, textarea {
            direction: rtl;
            text-align: right;
        }
        
        /* טבלאות RTL */
        table {
            direction: rtl;
            text-align: right;
        }
        
        /* DataFrame RTL */
        [data-testid="stDataFrame"] {
            direction: rtl;
        }
        
        [data-testid="stDataFrame"] table {
            direction: rtl;
            text-align: right;
        }
        
        [data-testid="stDataFrame"] th {
            text-align: right;
            direction: rtl;
        }
        
        [data-testid="stDataFrame"] td {
            text-align: right;
            direction: rtl;
        }
        
        /* Info boxes */
        .stInfo {
            background-color: #E6F2FF;
            border-right: 4px solid #0066CC;
            border-left: none;
            border-radius: 8px;
            padding: 1rem;
            direction: rtl;
            text-align: right;
        }
        
        /* Success boxes */
        .stSuccess {
            background-color: #E6F2FF;
            border-right: 4px solid #0066CC;
            border-left: none;
            border-radius: 8px;
            direction: rtl;
            text-align: right;
        }
        
        /* Warning boxes */
        .stWarning {
            background-color: #FFF4E6;
            border-right: 4px solid #FF9900;
            border-left: none;
            border-radius: 8px;
            direction: rtl;
            text-align: right;
        }
        
        /* Error boxes */
        .stError {
            background-color: #FFE6E6;
            border-right: 4px solid #CC0000;
            border-left: none;
            border-radius: 8px;
            direction: rtl;
            text-align: right;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            direction: rtl;
            text-align: right;
            color: #0066CC;
            font-weight: bold;
        }
        
        [data-testid="stMetricLabel"] {
            direction: rtl;
            text-align: right;
            color: #333333;
        }
        
        /* Tabs RTL */
        .stTabs [data-baseweb="tab-list"] {
            direction: rtl;
        }
        
        /* Expander RTL */
        .streamlit-expanderHeader {
            direction: rtl;
            text-align: right;
        }
        
        /* Cards */
        .opportunity-card {
            background-color: #FFFFFF;
            padding: 1.5rem;
            border-radius: 10px;
            border-right: 4px solid #0066CC;
            border-left: none;
            margin: 1rem 0;
            box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);
            direction: rtl;
            text-align: right;
        }
        
        /* Progress bar */
        .stProgress > div > div > div {
            background-color: #0066CC;
        }
        
        /* Selectbox RTL */
        select {
            direction: rtl;
            text-align: right;
        }
        
        /* Number input RTL */
        input[type="number"] {
            direction: ltr;
            text-align: left;
        }
        
        /* Date input RTL */
        [data-baseweb="input"] {
            direction: rtl;
        }
        
        /* Slider RTL */
        .stSlider {
            direction: rtl;
        }
        
        /* Footer */
        footer {
            direction: rtl;
            text-align: center;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    <script>
        // שינוי שם "app" ל-"DeltaMix" בתפריט הניווט
        function changeAppNameToDeltaMix() {
            const navLinks = document.querySelectorAll('[data-testid="stSidebarNav"] a');
            navLinks.forEach(link => {
                const href = link.getAttribute('href');
                const text = link.textContent.trim();
                // אם הקישור הוא ל-deltamix.py או ל-/, שנה את הטקסט ל"DeltaMix"
                if (href && (href.includes('deltamix.py') || href === '/' || text.toLowerCase() === 'app' || text.toLowerCase() === 'deltamix')) {
                    if (text !== 'DeltaMix') {
                        link.textContent = 'DeltaMix';
                    }
                }
            });
        }
        
        // הרצה מיידית ואחרי טעינת הדף
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', changeAppNameToDeltaMix);
        } else {
            changeAppNameToDeltaMix();
        }
        
        // הרצה גם אחרי ש-Streamlit מעדכן את הדף
        setTimeout(changeAppNameToDeltaMix, 100);
        setTimeout(changeAppNameToDeltaMix, 500);
        setTimeout(changeAppNameToDeltaMix, 1000);
        
        // מאזין לשינויים ב-DOM
        const observer = new MutationObserver(function(mutations) {
            changeAppNameToDeltaMix();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    </script>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """אתחול משתני session state"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'analysis_done' not in st.session_state:
        st.session_state.analysis_done = False
    if 'stock_data' not in st.session_state:
        st.session_state.stock_data = None
    if 'reference_data' not in st.session_state:
        st.session_state.reference_data = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'symbols' not in st.session_state:
        st.session_state.symbols = []
    if 'engine' not in st.session_state:
        st.session_state.engine = None
    if 'full_correlation_matrix' not in st.session_state:
        st.session_state.full_correlation_matrix = None
    if 'top_correlations' not in st.session_state:
        st.session_state.top_correlations = None
    if 'full_analysis_field' not in st.session_state:
        st.session_state.full_analysis_field = None

