"""
עמוד תוצאות ניתוח
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils import load_css, initialize_session_state

# טעינת CSS
load_css()

# אתחול session state
initialize_session_state()

# כותרת עמוד + כפתור רענון
col1, col2 = st.columns([5, 1])

with col1:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h1 style='color: #0066CC;'>📈 תוצאות ניתוח</h1>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.button("🔄 רענן", use_container_width=True, key="refresh_results"):
        st.rerun()

# בדיקת ניתוח
if not st.session_state.analysis_done:
    st.warning("⚠️ יש להריץ ניתוח קודם בעמוד 'ניתוח'")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ עבור לעמוד ניתוח", type="primary", use_container_width=True):
            st.switch_page("pages/2_🔬_ניתוח.py")
    st.stop()

# וידוא שיש מטריצות קורלציה
if not hasattr(st.session_state, 'combined_correlation_matrix') or st.session_state.combined_correlation_matrix is None:
    st.error("❌ לא נמצאו תוצאות ניתוח. יש להריץ ניתוח מחדש.")
    st.stop()

# קבלת המטריצות
price_matrix = st.session_state.price_correlation_matrix
volume_matrix = st.session_state.volume_correlation_matrix
combined_matrix = st.session_state.combined_correlation_matrix
engine = st.session_state.engine

# הסבר על החישובים
with st.expander("🧮 הסבר על החישובים והלוגיקה", expanded=False):
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h3 style='color: #0066CC;'>איך עובד הניתוח?</h3>
        
        <h4 style='color: #0066CC; margin-top: 1rem;'>1. מטריצת קורלציה 500×500</h4>
        <p>המערכת מחשבת קורלציה בין <strong>כל מניה לכל מניה אחרת</strong>.</p>
        <ul>
            <li><strong>קורלציית מחיר</strong>: קורלציה בין מחירי Adj Close של שתי מניות</li>
            <li><strong>קורלציית נפח</strong>: קורלציה בין נפחי המסחר של שתי מניות</li>
            <li><strong>קורלציה משולבת</strong>: מכפלת שתי הקורלציות (רק אם שתיהן חיוביות)</li>
        </ul>
        
        <h4 style='color: #0066CC; margin-top: 1rem;'>2. שלוש אופציות ניתוח</h4>
        <ul>
            <li><strong>אופציה 1</strong>: מחיר בלבד (Adj Close)</li>
            <li><strong>אופציה 2</strong>: נפח בלבד (Volume)</li>
            <li><strong>אופציה 3</strong>: משולב - מכפלה רק אם שתיהן חיוביות</li>
        </ul>
        
        <h4 style='color: #0066CC; margin-top: 1rem;'>3. תשואות</h4>
        <ul>
            <li><strong>תשואה יומית</strong>: (מחיר היום - מחיר אתמול) / מחיר אתמול × 100</li>
            <li><strong>תשואה מצטברת</strong>: (מחיר היום - מחיר ראשון) / מחיר ראשון × 100</li>
            <li><strong>תשואה שנתית</strong>: תשואה מצטברת / מספר שנים</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# טאבים
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 קורלציות גבוהות",
    "🎯 בחר מניית ייחוס",
    "📊 מטריצת קורלציה",
    "💰 תשואות",
    "⏱️ קורלציות לפי תאריך"
])

# טאב 1: קורלציות גבוהות
with tab1:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h2 style='color: #0066CC;'>🏆 הקורלציות הגבוהות ביותר</h2>
        <p>זוגות המניות עם הקורלציה הגבוהה ביותר</p>
    </div>
    """, unsafe_allow_html=True)
    
    if hasattr(st.session_state, 'top_correlations') and st.session_state.top_correlations is not None:
        top_corr = st.session_state.top_correlations
        
        # הצגת סטטיסטיקות
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("מספר זוגות", len(top_corr))
        
        with col2:
            if len(top_corr) > 0:
                st.metric("קורלציה ממוצעת", f"{top_corr['קורלציה'].mean():.3f}")
        
        with col3:
            if len(top_corr) > 0:
                st.metric("קורלציה מקסימלית", f"{top_corr['קורלציה'].max():.3f}")
        
        # טבלה
        st.dataframe(top_corr, use_container_width=True, height=500)
        
        # הורדה
        csv = top_corr.to_csv(index=False)
        st.download_button(
            "📥 הורד קורלציות גבוהות (CSV)",
            csv,
            f"top_correlations_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
        
        # גרף
        if len(top_corr) > 0:
            st.markdown("### גרף 20 הקורלציות הגבוהות ביותר")
            
            top_20 = top_corr.head(20).copy()
            top_20['זוג'] = top_20['מניה 1'] + ' ↔ ' + top_20['מניה 2']
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=top_20['זוג'],
                y=top_20['קורלציה'],
                marker_color='#0066CC'
            ))
            
            fig.update_layout(
                title="20 זוגות המניות עם הקורלציה הגבוהה ביותר",
                xaxis_title="זוג מניות",
                yaxis_title="קורלציה",
                height=500,
                xaxis={'tickangle': -45}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("אין נתוני קורלציות גבוהות")

# טאב 2: בחירת מניית ייחוס
with tab2:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h2 style='color: #0066CC;'>🎯 בחר מניית ייחוס</h2>
        <p>בחר מניה אחת ותראה את הקורלציות שלה מול כל המניות האחרות</p>
    </div>
    """, unsafe_allow_html=True)
    
    # בחירת מניה
    reference_stock = st.selectbox(
        "בחר מניית ייחוס",
        options=combined_matrix.columns.tolist(),
        help="בחר מניה לראות את הקורלציות שלה מול כל המניות"
    )
    
    if reference_stock:
        # חילוץ קורלציות של המניה הנבחרת
        correlations_with_ref = combined_matrix[reference_stock].copy()
        
        # מיון לפי קורלציה (הגבוהה ביותר ראשון)
        correlations_with_ref = correlations_with_ref.sort_values(ascending=False)
        
        # הצגה
        st.success(f"מציג קורלציות של **{reference_stock}** מול כל המניות")
        
        # טבלה
        df_ref = pd.DataFrame({
            'מניה': correlations_with_ref.index,
            'קורלציה': correlations_with_ref.values
        })
        
        # הסר את המניה עצמה (קורלציה של 1)
        df_ref = df_ref[df_ref['מניה'] != reference_stock]
        
        # סטטיסטיקות
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            positive = (df_ref['קורלציה'] > 0).sum()
            st.metric("קורלציות חיוביות", positive)
        
        with col2:
            negative = (df_ref['קורלציה'] < 0).sum()
            st.metric("קורלציות שליליות", negative)
        
        with col3:
            avg_corr = df_ref['קורלציה'].mean()
            st.metric("קורלציה ממוצעת", f"{avg_corr:.3f}")
        
        with col4:
            max_corr = df_ref['קורלציה'].max()
            st.metric("קורלציה מקסימלית", f"{max_corr:.3f}")
        
        st.dataframe(df_ref, use_container_width=True, height=500)
        
        # גרף
        st.markdown("### 20 המניות עם הקורלציה הגבוהה ביותר")
        
        fig = go.Figure()
        top_20 = df_ref.head(20)
        fig.add_trace(go.Bar(
            x=top_20['מניה'],
            y=top_20['קורלציה'],
            marker_color='#0066CC'
        ))
        
        fig.update_layout(
            title=f"20 המניות עם הקורלציה הגבוהה ביותר ל-{reference_stock}",
            xaxis_title="מניה",
            yaxis_title="קורלציה",
            height=500,
            xaxis={'tickangle': -45}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # הורדה
        csv = df_ref.to_csv(index=False)
        st.download_button(
            "📥 הורד נתונים (CSV)",
            csv,
            f"correlations_{reference_stock}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

# טאב 3: מטריצת קורלציה
with tab3:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h2 style='color: #0066CC;'>📊 מטריצת קורלציה מלאה</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # בחירת סוג מטריצה
    matrix_type = st.radio(
        "בחר סוג מטריצה",
        options=["קורלציה משולבת", "קורלציית מחיר", "קורלציית נפח"],
        horizontal=True
    )
    
    if matrix_type == "קורלציית מחיר":
        display_matrix = price_matrix
    elif matrix_type == "קורלציית נפח":
        display_matrix = volume_matrix
    else:
        display_matrix = combined_matrix
    
    # סטטיסטיקות
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("מספר מניות", len(display_matrix))
    
    with col2:
        total_corr = len(display_matrix) * (len(display_matrix) - 1) // 2
        st.metric("סה\"כ קורלציות", f"{total_corr:,}")
    
    with col3:
        # קורלציה ממוצעת (ללא האלכסון)
        mask = np.triu(np.ones_like(display_matrix, dtype=bool), k=1)
        avg_corr = display_matrix.values[mask].mean()
        st.metric("קורלציה ממוצעת", f"{avg_corr:.3f}")
    
    with col4:
        max_corr = display_matrix.values[mask].max()
        st.metric("קורלציה מקסימלית", f"{max_corr:.3f}")
    
    # Heatmap - רק אם המטריצה לא גדולה מדי
    if len(display_matrix) <= 100:
        st.markdown("### Heatmap")
        
        fig = px.imshow(
            display_matrix.values,
            labels=dict(x="מניה", y="מניה", color="קורלציה"),
            x=display_matrix.columns,
            y=display_matrix.index,
            color_continuous_scale="RdBu_r",
            aspect="auto",
            zmin=-1,
            zmax=1
        )
        
        fig.update_layout(
            title=f"מטריצת {matrix_type}",
            height=800
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"💡 המטריצה גדולה מדי ({len(display_matrix)}×{len(display_matrix)}) להצגת Heatmap. הורד את המטריצה לצפייה חיצונית.")
    
    # הורדת מטריצה
    st.markdown("### הורדת מטריצה")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = display_matrix.to_csv()
        st.download_button(
            "📥 הורד מטריצה (CSV)",
            csv,
            f"correlation_matrix_{matrix_type}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        try:
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                display_matrix.to_excel(writer, sheet_name=matrix_type)
            excel_data = output.getvalue()
            
            st.download_button(
                "📥 הורד מטריצה (Excel)",
                excel_data,
                f"correlation_matrix_{matrix_type}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except:
            st.info("💡 הורדת Excel דורשת התקנת openpyxl")

# טאב 4: תשואות
with tab4:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h2 style='color: #0066CC;'>💰 תשואות</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # חישוב תשואות
    if st.session_state.stock_data is not None:
        with st.spinner("מחשב תשואות..."):
            returns_data = engine.calculate_returns(st.session_state.stock_data)
        
        daily_returns = returns_data['daily_returns']
        cumulative_returns = returns_data['cumulative_returns']
        annualized_returns = returns_data['annualized_returns']
        
        # סטטיסטיקות כלליות
        st.markdown("### סטטיסטיקות כלליות")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_annual = annualized_returns.mean()
            st.metric("תשואה שנתית ממוצעת", f"{avg_annual:.2f}%")
        
        with col2:
            median_annual = annualized_returns.median()
            st.metric("תשואה שנתית חציונית", f"{median_annual:.2f}%")
        
        with col3:
            best_stock = annualized_returns.idxmax()
            best_return = annualized_returns.max()
            st.metric("תשואה שנתית מקסימלית", f"{best_return:.2f}%", delta=best_stock)
        
        with col4:
            worst_stock = annualized_returns.idxmin()
            worst_return = annualized_returns.min()
            st.metric("תשואה שנתית מינימלית", f"{worst_return:.2f}%", delta=worst_stock)
        
        # טבלת תשואות
        st.markdown("### טבלת תשואות למניות")
        
        # בניית טבלה
        returns_table = pd.DataFrame({
            'מניה': annualized_returns.index,
            'תשואה יומית ממוצעת (%)': [daily_returns[s].mean() for s in annualized_returns.index],
            'תשואה מצטברת (%)': [cumulative_returns[s].iloc[-1] for s in annualized_returns.index],
            'תשואה שנתית (%)': annualized_returns.values
        })
        
        # מיון לפי תשואה שנתית
        returns_table = returns_table.sort_values('תשואה שנתית (%)', ascending=False)
        
        # עיגול
        returns_table['תשואה יומית ממוצעת (%)'] = returns_table['תשואה יומית ממוצעת (%)'].round(3)
        returns_table['תשואה מצטברת (%)'] = returns_table['תשואה מצטברת (%)'].round(2)
        returns_table['תשואה שנתית (%)'] = returns_table['תשואה שנתית (%)'].round(2)
        
        st.dataframe(returns_table, use_container_width=True, height=500)
        
        # גרף התפלגות תשואות
        st.markdown("### התפלגות תשואות שנתיות")
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=annualized_returns.values,
            nbinsx=50,
            marker_color='#0066CC'
        ))
        
        fig.update_layout(
            title="התפלגות תשואות שנתיות",
            xaxis_title="תשואה שנתית (%)",
            yaxis_title="מספר מניות",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # גרף תשואות מצטברות לאורך זמן
        st.markdown("### תשואות מצטברות לאורך זמן (10 מניות מובילות)")
        
        # בחר 10 מניות עם התשואה הגבוהה ביותר
        top_10_stocks = returns_table.head(10)['מניה'].tolist()
        
        fig = go.Figure()
        for stock in top_10_stocks:
            fig.add_trace(go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns[stock],
                mode='lines',
                name=stock
            ))
        
        fig.update_layout(
            title="תשואות מצטברות לאורך זמן - 10 המניות המובילות",
            xaxis_title="תאריך",
            yaxis_title="תשואה מצטברת (%)",
            height=600,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # הורדה
        csv = returns_table.to_csv(index=False)
        st.download_button(
            "📥 הורד טבלת תשואות (CSV)",
            csv,
            f"returns_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
    else:
        st.warning("⚠️ אין נתוני מניות זמינים לחישוב תשואות")

# טאב 5: קורלציות לפי תאריך
with tab5:
    st.markdown("""
    <div style='direction: rtl; text-align: right;'>
        <h2 style='color: #0066CC;'>⏱️ קורלציות לפי תאריך</h2>
        <p>הצג איך הקורלציות משתנות לאורך זמן</p>
    </div>
    """, unsafe_allow_html=True)
    
    # בדיקה אם יש נתוני rolling correlations
    if (hasattr(st.session_state, 'price_rolling_correlations') and 
        st.session_state.price_rolling_correlations is not None):
        
        price_rolling = st.session_state.price_rolling_correlations
        volume_rolling = st.session_state.volume_rolling_correlations
        rolling_window = st.session_state.rolling_window
        
        st.success(f"✅ קורלציות גליליות חושבו עם חלון של {rolling_window} ימים")
        
        # בחירת זוג מניות
        st.markdown("### בחר זוג מניות לצפייה")
        
        col1, col2 = st.columns(2)
        
        available_stocks = list(price_rolling.keys())
        
        with col1:
            stock1 = st.selectbox(
                "מניה 1",
                options=available_stocks,
                key="rolling_stock1"
            )
        
        with col2:
            stock2 = st.selectbox(
                "מניה 2",
                options=available_stocks,
                key="rolling_stock2"
            )
        
        if stock1 and stock2 and stock1 != stock2:
            # חילוץ הקורלציות לאורך זמן
            if stock2 in price_rolling[stock1].columns:
                price_corr_series = price_rolling[stock1][stock2]
                volume_corr_series = volume_rolling[stock1][stock2]
                
                # הצגה
                st.markdown(f"### קורלציות {stock1} ↔ {stock2} לאורך זמן")
                
                # סטטיסטיקות
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_price = price_corr_series.mean()
                    st.metric("קורלציית מחיר ממוצעת", f"{avg_price:.3f}")
                
                with col2:
                    avg_volume = volume_corr_series.mean()
                    st.metric("קורלציית נפח ממוצעת", f"{avg_volume:.3f}")
                
                with col3:
                    last_price = price_corr_series.iloc[-1]
                    st.metric("קורלציית מחיר אחרונה", f"{last_price:.3f}")
                
                with col4:
                    last_volume = volume_corr_series.iloc[-1]
                    st.metric("קורלציית נפח אחרונה", f"{last_volume:.3f}")
                
                # גרף
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=price_corr_series.index,
                    y=price_corr_series.values,
                    mode='lines',
                    name='קורלציית מחיר',
                    line=dict(color='#0066CC', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=volume_corr_series.index,
                    y=volume_corr_series.values,
                    mode='lines',
                    name='קורלציית נפח',
                    line=dict(color='#FF6B6B', width=2)
                ))
                
                # קו אפס
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                
                fig.update_layout(
                    title=f"קורלציות {stock1} ↔ {stock2} לאורך זמן (חלון {rolling_window} ימים)",
                    xaxis_title="תאריך",
                    yaxis_title="קורלציה",
                    height=600,
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # טבלה
                st.markdown("### טבלת נתונים")
                
                df_display = pd.DataFrame({
                    'תאריך': price_corr_series.index,
                    'קורלציית מחיר': price_corr_series.values,
                    'קורלציית נפח': volume_corr_series.values
                })
                
                df_display['קורלציית מחיר'] = df_display['קורלציית מחיר'].round(4)
                df_display['קורלציית נפח'] = df_display['קורלציית נפח'].round(4)
                
                st.dataframe(df_display, use_container_width=True, height=400)
                
                # הורדה
                csv = df_display.to_csv(index=False)
                st.download_button(
                    "📥 הורד נתונים (CSV)",
                    csv,
                    f"rolling_correlations_{stock1}_{stock2}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            else:
                st.warning(f"⚠️ לא נמצאו נתוני קורלציה עבור {stock1} ↔ {stock2}")
        
        elif stock1 == stock2:
            st.info("💡 בחר שתי מניות שונות")
        
        # אופציה נוספת: הצגת top correlations בתאריך מסוים
        st.markdown("---")
        st.markdown("### בחר תאריך לראות קורלציות גבוהות באותו יום")
        
        # בחירת תאריך
        available_dates = sorted(list(price_rolling[available_stocks[0]].index))
        
        selected_date = st.selectbox(
            "בחר תאריך",
            options=available_dates,
            index=len(available_dates) - 1,  # תאריך אחרון
            format_func=lambda x: x.strftime('%Y-%m-%d')
        )
        
        if selected_date:
            st.markdown(f"### קורלציות גבוהות ב-{selected_date.strftime('%Y-%m-%d')}")
            
            # חילוץ כל הקורלציות לתאריך זה
            correlations_on_date = []
            
            for stock_a in available_stocks:
                for stock_b in available_stocks:
                    if stock_a < stock_b:  # למנוע כפילויות
                        if stock_b in price_rolling[stock_a].columns:
                            price_corr = price_rolling[stock_a][stock_b].loc[selected_date]
                            volume_corr = volume_rolling[stock_a][stock_b].loc[selected_date]
                            
                            # חישוב קורלציה משולבת
                            if price_corr > 0 and volume_corr > 0:
                                combined_corr = price_corr * volume_corr
                            else:
                                combined_corr = 0
                            
                            correlations_on_date.append({
                                'מניה 1': stock_a,
                                'מניה 2': stock_b,
                                'קורלציית מחיר': price_corr,
                                'קורלציית נפח': volume_corr,
                                'קורלציה משולבת': combined_corr
                            })
            
            # יצירת DataFrame
            df_date = pd.DataFrame(correlations_on_date)
            df_date = df_date.sort_values('קורלציה משולבת', ascending=False)
            
            # עיגול
            df_date['קורלציית מחיר'] = df_date['קורלציית מחיר'].round(4)
            df_date['קורלציית נפח'] = df_date['קורלציית נפח'].round(4)
            df_date['קורלציה משולבת'] = df_date['קורלציה משולבת'].round(4)
            
            # סטטיסטיקות
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("סה\"כ זוגות", len(df_date))
            
            with col2:
                avg = df_date['קורלציה משולבת'].mean()
                st.metric("קורלציה משולבת ממוצעת", f"{avg:.3f}")
            
            with col3:
                max_corr = df_date['קורלציה משולבת'].max()
                st.metric("קורלציה משולבת מקסימלית", f"{max_corr:.3f}")
            
            # הצגת top 50
            st.markdown("#### 50 הקורלציות הגבוהות ביותר")
            st.dataframe(df_date.head(50), use_container_width=True, height=500)
            
            # גרף
            fig = go.Figure()
            top_20 = df_date.head(20)
            top_20['זוג'] = top_20['מניה 1'] + ' ↔ ' + top_20['מניה 2']
            
            fig.add_trace(go.Bar(
                x=top_20['זוג'],
                y=top_20['קורלציה משולבת'],
                marker_color='#0066CC'
            ))
            
            fig.update_layout(
                title=f"20 הקורלציות הגבוהות ביותר ב-{selected_date.strftime('%Y-%m-%d')}",
                xaxis_title="זוג מניות",
                yaxis_title="קורלציה משולבת",
                height=500,
                xaxis={'tickangle': -45}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # הורדה
            csv = df_date.to_csv(index=False)
            st.download_button(
                "📥 הורד קורלציות לתאריך זה (CSV)",
                csv,
                f"correlations_{selected_date.strftime('%Y%m%d')}.csv",
                "text/csv"
            )
    
    else:
        st.info("""
        💡 **לא חושבו קורלציות לאורך זמן**
        
        כדי להשתמש בתכונה זו:
        1. עבור לעמוד 'ניתוח'
        2. סמן את האופציה "חשב קורלציות לאורך זמן"
        3. בחר גודל חלון
        4. הרץ את הניתוח
        
        זה יאפשר לך לראות איך הקורלציות משתנות לאורך זמן.
        """)
