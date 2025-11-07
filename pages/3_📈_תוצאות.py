"""
עמוד תוצאות ניתוח
"""

import streamlit as st
import pandas as pd
import numpy as np
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
engine = st.session_state.engine

# הסבר על החישובים
with st.expander("🧮 הסבר על החישובים והלוגיקה", expanded=False):
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h3 style='color: #0066CC;'>איך עובד הניתוח?</h3>
        
        <h4 style='color: #0066CC; margin-top: 1rem;'>1. קורלציה</h4>
        <p><strong>קורלציה</strong> היא מדד סטטיסטי שמודד עד כמה שני משתנים נעים יחד.</p>
        <ul>
            <li><strong>קורלציית מחיר</strong>: מודדת עד כמה תנועות המחיר של המניה דומות לתנועות מניית הייחוס (SPY).
                <br>🔹 המערכת מחשבת קורלציה על <strong>אחוזי שינוי יומיים</strong> (תשואות), לא על מחירים גולמיים.
                <br>🔹 זה מבטיח שנמדוד את הדמיון בין <strong>התנועות</strong>, לא רק את רמות המחירים.
            </li>
            <li><strong>קורלציית נפח</strong>: מודדת עד כמה שינויים בנפח המסחר דומים למניית הייחוס.</li>
            <li><strong>קורלציה משולבת</strong> (calc_mode=3):
                <ul>
                    <li>מכפלה של קורלציית מחיר × קורלציית נפח</li>
                    <li>רק אם שתיהן חיוביות (אחרת = 0)</li>
                    <li>טווח: 0 עד 1</li>
                    <li>ערכים טיפוסיים: 0.2-0.6</li>
                    <li>ערכים מעל 0.7: קורלציה חזקה מאוד ⚠️</li>
                </ul>
            </li>
        </ul>
        
        <h4 style='color: #0066CC; margin-top: 1rem;'>2. יחס נפח</h4>
        <p><strong>יחס נפח</strong> = ממוצע נע של נפח המסחר / נפח נוכחי</p>
        <ul>
            <li>ערך > 1.01 (סף + 1%): נפח גבוה יותר מהרגיל = אות להזדמנות</li>
            <li>ערך < 1: נפח נמוך מהרגיל</li>
        </ul>
        
        <h4 style='color: #0066CC; margin-top: 1rem;'>3. סף מובהקות</h4>
        <p><strong>סף מובהקות</strong> (ברירת מחדל: 0.7) - רק ימים שבהם הקורלציה המשולבת >= 0.7 נחשבים "כשירים"</p>
        
        <h4 style='color: #0066CC; margin-top: 1rem;'>4. הזדמנויות UP</h4>
        <p>יום נחשב ל-<strong>"הזדמנות UP"</strong> כאשר:</p>
        <ul>
            <li>הקורלציה המשולבת >= סף מובהקות (0.7)</li>
            <li>יחס הנפח > סף מהותיות (1.01)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# בדיקת איכות הקורלציות
validation = engine.validate_correlations(results)

# הצגת מידע על איכות הקורלציות
if validation['average_correlation'] > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "ממוצע קורלציות",
            f"{validation['average_correlation']:.3f}",
            help="ממוצע כל הקורלציות המשולבות החיוביות"
        )
    
    with col2:
        st.metric(
            "חציון קורלציות", 
            f"{validation['median_correlation']:.3f}",
            help="חציון הקורלציות המשולבות"
        )
    
    with col3:
        high_pct = validation['distribution']['high']
        total = sum(validation['distribution'].values())
        st.metric(
            "קורלציות גבוהות (0.7-0.9)",
            f"{high_pct:,}",
            delta=f"{high_pct/total*100:.1f}%" if total > 0 else "0%"
        )
    
    with col4:
        very_high = validation['distribution']['very_high']
        st.metric(
            "קורלציות מאוד גבוהות (>0.9)",
            f"{very_high:,}",
            delta="⚠️ חשוד" if very_high > total * 0.1 else "✓ תקין",
            delta_color="inverse" if very_high > total * 0.1 else "normal"
        )
    
    # אזהרה אם יש קורלציות חשודות
    if validation['suspicious_high']:
        st.warning(f"""
        ⚠️ **זוהו {len(validation['suspicious_high'])} מניות עם קורלציה מעל 0.95**
        
        זה עשוי להצביע על בעיה בחישוב. קורלציות מעל 0.95 הן נדירות מאוד בשוק האמיתי.
        """)

st.markdown("---")

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

# תצוגה מפורטת - כל המניות מעל הסף
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>📊 תצוגה מפורטת - כל המניות מעל הסף</h2>
</div>
""", unsafe_allow_html=True)

# בניית טבלה מפורטת
detailed_results = []
for symbol in results['statistics'].keys():
    # קורלציה אחרונה של כל סוג
    last_price_corr = results['price_correlations'][symbol].iloc[-1]
    last_volume_corr = results['volume_correlations'][symbol].iloc[-1]
    last_combined_corr = results['combined_correlations'][symbol].iloc[-1]
    last_volume_ratio = results['volume_ratios'][symbol].iloc[-1]
    
    # רק מניות מעל הסף
    if last_combined_corr >= engine.significance:
        detailed_results.append({
            'מניה': symbol,
            'קורלציית מחיר': last_price_corr,
            'קורלציית נפח': last_volume_corr,
            'קורלציה משולבת': last_combined_corr,
            'יחס נפח': last_volume_ratio,
            'ימים UP': results['statistics'][symbol]['UP'],
            'אחוז UP': results['statistics'][symbol]['UP_PCT'],
            'סה"כ ימים': results['statistics'][symbol]['TOTAL']
        })

if detailed_results:
    df_detailed = pd.DataFrame(detailed_results)
    df_detailed = df_detailed.sort_values('קורלציה משולבת', ascending=False)
    
    st.success(f"✅ נמצאו **{len(df_detailed)}** מניות מעל הסף ({engine.significance})")
    
    # סינון
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_combined = st.slider(
            "קורלציה משולבת מינימלית",
            min_value=0.0,
            max_value=1.0,
            value=float(engine.significance),
            step=0.05,
            help="סנן מניות לפי קורלציה משולבת מינימלית"
        )
    
    with col2:
        min_up_days = st.number_input(
            "מינימום ימי UP",
            min_value=0,
            value=0,
            help="סנן מניות לפי מספר מינימלי של ימי הזדמנויות"
        )
    
    with col3:
        search_symbol = st.text_input(
            "חפש מניה",
            "",
            help="חפש מניה ספציפית לפי סימול"
        )
    
    # החלת סינונים
    df_filtered = df_detailed[df_detailed['קורלציה משולבת'] >= min_combined]
    if min_up_days > 0:
        df_filtered = df_filtered[df_filtered['ימים UP'] >= min_up_days]
    if search_symbol:
        df_filtered = df_filtered[df_filtered['מניה'].str.contains(search_symbol.upper())]
    
    # עיצוב הטבלה
    df_display = df_filtered.copy()
    df_display['קורלציית מחיר'] = df_display['קורלציית מחיר'].apply(lambda x: f"{x:.3f}")
    df_display['קורלציית נפח'] = df_display['קורלציית נפח'].apply(lambda x: f"{x:.3f}")
    df_display['קורלציה משולבת'] = df_display['קורלציה משולבת'].apply(lambda x: f"{x:.3f}")
    df_display['יחס נפח'] = df_display['יחס נפח'].apply(lambda x: f"{x:.3f}")
    df_display['אחוז UP'] = df_display['אחוז UP'].apply(lambda x: f"{x*100:.1f}%")
    
    st.dataframe(df_display, use_container_width=True, height=400)
    
    # הסבר על העמודות
    with st.expander("ℹ️ הסבר על העמודות"):
        st.markdown("""
        <div style='direction: rtl; text-align: right;'>
        - **מניה**: סימול המניה
        - **קורלציית מחיר**: קורלציה בין תשואות המחיר של המניה למניית הייחוס (ערך אחרון)
        - **קורלציית נפח**: קורלציה בין שינויי הנפח של המניה למניית הייחוס (ערך אחרון)
        - **קורלציה משולבת**: מכפלה של קורלציית מחיר × קורלציית נפח (ערך אחרון)
        - **יחס נפח**: ממוצע נע של נפח / נפח נוכחי (ערך אחרון)
        - **ימים UP**: מספר הימים שבהם היו הזדמנויות (קורלציה מעל הסף + יחס נפח מעל הסף)
        - **אחוז UP**: אחוז הימים עם הזדמנויות מתוך כל הימים הכשירים
        - **סה"כ ימים**: סה"כ ימים כשירים (קורלציה מעל הסף)
        </div>
        """, unsafe_allow_html=True)
    
    # הורדה
    csv_detailed = df_filtered.to_csv(index=False)
    st.download_button(
        "📥 הורד טבלה מפורטת (CSV)",
        csv_detailed,
        f"detailed_correlations_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
else:
    st.info("לא נמצאו מניות מעל הסף")

st.markdown("---")

# הזדמנויות להיום
st.markdown("""
<div style='direction: rtl; text-align: right;'>
    <h2 style='color: #0066CC; margin-top: 2rem; margin-bottom: 1rem;'>🎯 הזדמנויות להיום</h2>
</div>
""", unsafe_allow_html=True)

opportunities = engine.find_today_opportunities(results)

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

tab1, tab2, tab3, tab4 = st.tabs(["התפלגות הזדמנויות", "קורלציות לאורך זמן", "היסטוגרמה", "התפלגות קורלציות"])

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

with tab4:
    # התפלגות קורלציות משולבות
    st.markdown('<div style="direction: rtl; text-align: right; margin-bottom: 1rem;">התפלגות הקורלציות המשולבות לכל המניות</div>', unsafe_allow_html=True)
    
    # איסוף כל הקורלציות
    combined = results['combined_correlations']
    all_correlations = []
    
    for col in combined.columns:
        col_values = combined[col].values
        # רק ערכים תקינים (לא NaN ולא 0)
        valid_values = col_values[(~np.isnan(col_values)) & (col_values > 0)]
        all_correlations.extend(valid_values.tolist())
    
    if all_correlations:
        fig = go.Figure()
        
        # היסטוגרמה
        fig.add_trace(go.Histogram(
            x=all_correlations,
            nbinsx=50,
            marker_color='#0066CC',
            marker_line_color='#0052A3',
            marker_line_width=1,
            name='קורלציות משולבות'
        ))
        
        # קו אנכי בסף המובהקות
        fig.add_vline(
            x=engine.significance,
            line_dash="dash",
            line_color="red",
            annotation_text=f"סף מובהקות ({engine.significance})",
            annotation_position="top right"
        )
        
        fig.update_layout(
            title={
                'text': 'התפלגות הקורלציות המשולבות',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#0066CC'}
            },
            xaxis_title='קורלציה משולבת',
            yaxis_title='תדירות',
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Segoe UI', size=12),
            xaxis=dict(showgrid=True, gridcolor='#E6F2FF', range=[0, 1]),
            yaxis=dict(showgrid=True, gridcolor='#E6F2FF'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # סטטיסטיקות
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("ממוצע", f"{np.mean(all_correlations):.3f}")
        
        with col2:
            st.metric("חציון", f"{np.median(all_correlations):.3f}")
        
        with col3:
            st.metric("סטיית תקן", f"{np.std(all_correlations):.3f}")
        
        with col4:
            above_threshold = sum(1 for c in all_correlations if c >= engine.significance)
            pct = (above_threshold / len(all_correlations)) * 100
            st.metric("מעל הסף", f"{above_threshold:,} ({pct:.1f}%)")
        
        st.info("""
        📊 **איך לקרוא את הגרף:**
        - התפלגות תקינה צריכה להיות פרושה על טווח רחב (0.1-0.8)
        - ריכוז גבוה של קורלציות מעל 0.9 מצביע על בעיה אפשרית
        - הקו האדום מסמן את סף המובהקות שהוגדר
        """)
    else:
        st.warning("אין מספיק נתונים להצגת התפלגות")

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

