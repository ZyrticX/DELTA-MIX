"""
עמוד תוצאות ניתוח
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils import load_css, initialize_session_state

# טעינת CSS
load_css()

# אתחול session state
initialize_session_state()

# כותרת עמוד
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h1 style='color: #0066CC; margin-bottom: 2rem;'>📈 תוצאות ניתוח</h1>
</div>
""", unsafe_allow_html=True)

# בדיקת ניתוח
if not st.session_state.analysis_done:
    st.warning("⚠️ יש להריץ ניתוח קודם בעמוד 'ניתוח'")
    st.info("עבור לעמוד ניתוח כדי להריץ את הניתוח.")
    st.stop()

results = st.session_state.results

# סטטיסטיקה כללית
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📊 סטטיסטיקה כללית</h2>
</div>
""", unsafe_allow_html=True)

stats = results['statistics']

# חישוב סיכומים
total_up = sum(s['UP'] for s in stats.values())
total_down = sum(s['DOWN'] for s in stats.values())
total_total = sum(s['TOTAL'] for s in stats.values())

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "סה\"כ הזדמנויות UP",
        f"{total_up:,}",
        delta=f"{total_up/total_total*100:.1f}%" if total_total > 0 else "0%"
    )

with col2:
    st.metric(
        "סה\"כ ימים DOWN",
        f"{total_down:,}",
        delta=f"{total_down/total_total*100:.1f}%" if total_total > 0 else "0%",
        delta_color="inverse"
    )

with col3:
    st.metric(
        "סה\"כ ימים כשירים",
        f"{total_total:,}"
    )

with col4:
    st.metric(
        "מספר מניות",
        len(stats)
    )

st.markdown("---")

# טבלת מניות
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📋 פירוט למניות</h2>
</div>
""", unsafe_allow_html=True)

# יצירת DataFrame
df_stats = pd.DataFrame(stats).T
df_stats = df_stats.sort_values('UP', ascending=False)

# עיצוב
df_display = df_stats.copy()
df_display['UP_PCT'] = df_display['UP_PCT'].apply(lambda x: f"{x*100:.1f}%")
df_display['DOWN_PCT'] = df_display['DOWN_PCT'].apply(lambda x: f"{x*100:.1f}%")

# חיפוש וסינון
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div style="direction: rtl; text-align: right;">🔍 חפש מניה</div>', unsafe_allow_html=True)
    search = st.text_input("", "", key="search_stock", label_visibility="collapsed")

with col2:
    st.markdown('<div style="direction: rtl; text-align: right;">מינימום הזדמנויות</div>', unsafe_allow_html=True)
    min_opportunities = st.number_input("", min_value=0, value=0, key="min_opp", label_visibility="collapsed")

# סינון
if search:
    df_display = df_display[df_display.index.str.contains(search.upper())]

if min_opportunities > 0:
    df_display = df_display[df_display['UP'] >= min_opportunities]

# הצגה
st.dataframe(
    df_display,
    use_container_width=True,
    height=400
)

# הורדה
csv = df_display.to_csv()
st.download_button(
    "📥 הורד טבלה (CSV)",
    csv,
    "stocks_statistics.csv",
    "text/csv"
)

st.markdown("---")

# הזדמנויות להיום
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>🎯 הזדמנויות להיום</h2>
</div>
""", unsafe_allow_html=True)

opportunities = st.session_state.engine.find_today_opportunities(results)

if not opportunities:
    st.info("לא נמצאו הזדמנויות להיום")
else:
    st.success(f"נמצאו {len(opportunities)} הזדמנויות!")
    
    # הצגה בכרטיסים
    for i, opp in enumerate(opportunities[:10]):  # הצג רק 10 ראשונות
        with st.expander(f"🎯 {opp['symbol']} - קורלציה: {opp['correlation']:.3f}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("קורלציה", f"{opp['correlation']:.3f}")
            
            with col2:
                st.metric("יחס נפח", f"{opp['volume_ratio']:.3f}")
            
            with col3:
                st.metric("תאריך", opp['date'].strftime('%Y-%m-%d'))

st.markdown("---")

# גרפים
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📊 גרפים</h2>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["התפלגות הזדמנויות", "קורלציות לאורך זמן", "היסטוגרמה"])

with tab1:
    # גרף התפלגות הזדמנויות
    df_chart = pd.DataFrame({
        'Symbol': list(stats.keys()),
        'UP': [s['UP'] for s in stats.values()],
        'DOWN': [s['DOWN'] for s in stats.values()]
    })
    
    df_chart = df_chart.sort_values('UP', ascending=False).head(20)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_chart['Symbol'],
        y=df_chart['UP'],
        name='UP (הזדמנויות)',
        marker_color='#0066CC'
    ))
    
    fig.add_trace(go.Bar(
        x=df_chart['Symbol'],
        y=df_chart['DOWN'],
        name='DOWN (רגיל)',
        marker_color='#CCCCCC'
    ))
    
    fig.update_layout(
        title={
            'text': '20 המניות עם הכי הרבה הזדמנויות',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#0066CC'}
        },
        xaxis_title='מניה',
        yaxis_title='מספר ימים',
        barmode='stack',
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Segoe UI', size=12),
        xaxis=dict(showgrid=True, gridcolor='#E6F2FF'),
        yaxis=dict(showgrid=True, gridcolor='#E6F2FF'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # גרף קורלציות לאורך זמן
    combined = results['combined_correlations']
    
    st.markdown('<div style="direction: rtl; text-align: right; margin-bottom: 0.5rem;">בחר מניות להצגה</div>', unsafe_allow_html=True)
    selected_stocks = st.multiselect(
        "",
        options=list(combined.columns),
        default=list(combined.columns)[:5],
        max_selections=10,
        label_visibility="collapsed"
    )
    
    if selected_stocks:
        fig = go.Figure()
        
        for stock in selected_stocks:
            fig.add_trace(go.Scatter(
                x=combined.index,
                y=combined[stock],
                name=stock,
                mode='lines'
            ))
        
        fig.update_layout(
            title={
                'text': 'קורלציות משולבות לאורך זמן',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#0066CC'}
            },
            xaxis_title='תאריך',
            yaxis_title='קורלציה',
            height=500,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Segoe UI', size=12),
            xaxis=dict(showgrid=True, gridcolor='#E6F2FF'),
            yaxis=dict(showgrid=True, gridcolor='#E6F2FF'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # עדכון צבעי הקווים לכחול
        for i, trace in enumerate(fig.data):
            trace.line.color = '#0066CC' if i == 0 else f'rgba(0, 102, 204, {0.7 - i*0.1})'
        
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    # היסטוגרמה
    up_counts = [s['UP'] for s in stats.values()]
    
    fig = go.Figure(data=[go.Histogram(
        x=up_counts, 
        nbinsx=20,
        marker_color='#0066CC',
        marker_line_color='#0052A3',
        marker_line_width=1
    )])
    
    fig.update_layout(
        title={
            'text': 'התפלגות מספר ההזדמנויות למניה',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#0066CC'}
        },
        xaxis_title='מספר הזדמנויות',
        yaxis_title='מספר מניות',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Segoe UI', size=12),
        xaxis=dict(showgrid=True, gridcolor='#E6F2FF'),
        yaxis=dict(showgrid=True, gridcolor='#E6F2FF'),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ייצוא תוצאות
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>💾 ייצוא תוצאות</h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 ייצא ל-Excel", use_container_width=True):
        try:
            from io import BytesIO
            
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # סטטיסטיקות
                df_stats = pd.DataFrame(results['statistics']).T
                df_stats.to_excel(writer, sheet_name='Statistics')
                
                # קורלציות שער
                results['price_correlations'].to_excel(writer, sheet_name='Price_Correlations')
                
                # קורלציות מחזור
                results['volume_correlations'].to_excel(writer, sheet_name='Volume_Correlations')
                
                # קורלציות משולבות
                results['combined_correlations'].to_excel(writer, sheet_name='Combined_Correlations')
                
                # יחסי נפח
                results['volume_ratios'].to_excel(writer, sheet_name='Volume_Ratios')
            
            output.seek(0)
            
            st.download_button(
                "⬇️ הורד קובץ Excel",
                output,
                f"correlation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success("✅ הקובץ מוכן להורדה!")
            
        except Exception as e:
            st.error(f"שגיאה בייצוא: {str(e)}")

with col2:
    csv = df_stats.to_csv()
    st.download_button(
        "📄 ייצא ל-CSV",
        csv,
        f"correlation_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv"
    )

with col3:
    st.info("📊 ייצוא גרפים - בקרוב...")

