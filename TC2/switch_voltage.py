import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy import stats
import os


def show():
    # 读取 CSV
    current_dir = os.path.dirname(os.path.abspath(__file__))

    main_csv_path = os.path.join(current_dir, "..", "data", "TC2-切换电压统计结果-v5-20260427-2.csv")
    main_csv_path = os.path.normpath(main_csv_path)

    summary_csv_path = os.path.join(current_dir, "..", "data", "TC2-切换电压_分组汇总-v5-20260427-2.csv")
    summary_csv_path = os.path.normpath(summary_csv_path)

    try:
        if not os.path.exists(main_csv_path):
            st.error(f"Main CSV file not found: {main_csv_path}")
            return

        # 读取主数据
        df = pd.read_csv(main_csv_path, encoding='utf-8')
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')

        # 读取分组汇总数据（包含中位数和均值）
        n_median_map = {}
        p_median_map = {}
        n_avg_map = {}
        p_avg_map = {}

        if os.path.exists(summary_csv_path):
            df_summary = pd.read_csv(summary_csv_path, encoding='utf-8')
            df_summary.columns = df_summary.columns.str.strip().str.replace('\ufeff', '')
            df_summary = df_summary.rename(columns={
                '所属项目': 'Project Name',
                '电压条件': 'Voltage Condition',
                'N-switch中位数(V)': 'N-switch Median (V)',
                'P-switch中位数(V)': 'P-switch Median (V)',
                'N-switch均值(V)': 'N-switch Average (V)',
                'P-switch均值(V)': 'P-switch Average (V)',
            })
            # 创建映射
            for _, row in df_summary.iterrows():
                key = f"{row['Project Name']}|{row['Voltage Condition']}"
                n_median_map[key] = row.get('N-switch Median (V)', 'N/A')
                p_median_map[key] = row.get('P-switch Median (V)', 'N/A')
                n_avg_map[key] = row.get('N-switch Average (V)', 'N/A')
                p_avg_map[key] = row.get('P-switch Average (V)', 'N/A')

        # 重命名主数据的列
        df = df.rename(columns={
            '所属项目': 'Project Name',
            '电压条件': 'Voltage Condition',
            '正切换电压(V)': 'Positive Voltage (V)',
            '负切换电压(V)': 'Negative Voltage (V)',
            '文件名': 'File Name',
        })

        # 添加中位数和均值的列
        df['Match Key'] = df['Project Name'] + '|' + df['Voltage Condition']
        df['N-switch Median (V)'] = df['Match Key'].map(n_median_map)
        df['P-switch Median (V)'] = df['Match Key'].map(p_median_map)
        df['N-switch Average (V)'] = df['Match Key'].map(n_avg_map)
        df['P-switch Average (V)'] = df['Match Key'].map(p_avg_map)

        # 全局样式：把所有下拉选项的红色背景改成浅蓝色
        st.markdown("""
            <style>
                /* 下拉框选中项（tag）的背景色 - 浅蓝色 */
                span[data-baseweb="tag"] {
                    background-color: #e6f0ff !important;
                    border-color: #b3d4ff !important;
                }
                span[data-baseweb="tag"] svg {
                    fill: #4a8bbf !important;
                }
                /* 下拉框选项悬停背景 */
                div[data-baseweb="select"] li:hover {
                    background-color: #f0f5ff !important;
                }
                /* 下拉框选中项的高亮背景 */
                div[data-baseweb="select"] li[aria-selected="true"] {
                    background-color: #e6f0ff !important;
                }
                /* 多选下拉框的选中项 */
                div[data-baseweb="select"] [role="listbox"] div[data-highlighted="true"] {
                    background-color: #e6f0ff !important;
                }
                /* 单选下拉框的选中项 */
                div[data-baseweb="select"] div[role="option"][aria-selected="true"] {
                    background-color: #e6f0ff !important;
                }
                /* 所有 select 相关的红色改成浅蓝色 */
                .stMultiSelect [data-baseweb="tag"] {
                    background-color: #e6f0ff !important;
                }
                /* radio 按钮选中时的颜色 */
                div[role="radiogroup"] input:checked {
                    accent-color: #4a8bbf !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # ========== 联动筛选器 ==========
        # 获取所有选项
        all_projects = sorted(df['Project Name'].dropna().unique().tolist())
        all_voltages = sorted(df['Voltage Condition'].dropna().unique().tolist())

        # 初始化 session state 存储筛选状态
        if 'tc2_selected_projects' not in st.session_state:
            st.session_state.tc2_selected_projects = all_projects
        if 'tc2_selected_voltages' not in st.session_state:
            st.session_state.tc2_selected_voltages = all_voltages

        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            # 根据当前选择的电压条件，计算可用的项目选项
            if st.session_state.tc2_selected_voltages:
                available_projects = df[df['Voltage Condition'].isin(st.session_state.tc2_selected_voltages)][
                    'Project Name'].dropna().unique().tolist()
            else:
                available_projects = all_projects
            available_projects = sorted(available_projects)

            selected_projects = st.multiselect(
                "Filter by Project Name",
                options=available_projects,
                default=[p for p in st.session_state.tc2_selected_projects if p in available_projects],
                placeholder="Select projects..."
            )
            st.session_state.tc2_selected_projects = selected_projects

        with col_filter2:
            # 根据当前选择的项目，计算可用的电压条件选项
            if st.session_state.tc2_selected_projects:
                available_voltages = df[df['Project Name'].isin(st.session_state.tc2_selected_projects)][
                    'Voltage Condition'].dropna().unique().tolist()
            else:
                available_voltages = all_voltages
            available_voltages = sorted(available_voltages)

            selected_voltages = st.multiselect(
                "Filter by Voltage Condition",
                options=available_voltages,
                default=[v for v in st.session_state.tc2_selected_voltages if v in available_voltages],
                placeholder="Select voltage conditions..."
            )
            st.session_state.tc2_selected_voltages = selected_voltages

        # 应用筛选
        filtered_df = df.copy()
        if st.session_state.tc2_selected_projects:
            filtered_df = filtered_df[filtered_df['Project Name'].isin(st.session_state.tc2_selected_projects)]
        if st.session_state.tc2_selected_voltages:
            filtered_df = filtered_df[filtered_df['Voltage Condition'].isin(st.session_state.tc2_selected_voltages)]

        if len(filtered_df) == 0:
            st.warning("No data available. Please adjust your filters.")
            return

        # ========== 提取原始数据用于拟合 ==========
        positive_values = filtered_df['Positive Voltage (V)'].dropna().tolist()
        negative_values = filtered_df['Negative Voltage (V)'].dropna().tolist()

        # 计算平均值
        avg_positive = np.mean(positive_values) if positive_values else None
        avg_negative = np.mean(negative_values) if negative_values else None

        # ========== 创建图表 ==========
        fig = go.Figure()

        # ----- 正电压：直方图 + KDE曲线 + 平均值竖线 -----
        if positive_values:
            fig.add_trace(go.Histogram(
                x=positive_values,
                name='Positive Switch',
                marker_color='#2E86AB',
                opacity=0.6,
                histnorm='probability density',
                nbinsx=30,
                legendgroup='Positive',
                showlegend=True
            ))

            if len(positive_values) > 1:
                kde_x = np.linspace(min(positive_values), max(positive_values), 200)
                kde = stats.gaussian_kde(positive_values)
                kde_y = kde(kde_x)
                fig.add_trace(go.Scatter(
                    x=kde_x,
                    y=kde_y,
                    name='Positive Switch (KDE Fit)',
                    line=dict(color='#2E86AB', width=2.5),
                    legendgroup='Positive',
                    showlegend=True,
                    mode='lines'
                ))

            if avg_positive is not None:
                fig.add_vline(
                    x=avg_positive,
                    line_width=2,
                    line_dash="dash",
                    line_color="#2E86AB",
                    opacity=0.8,
                    annotation_text=f"Avg P: {avg_positive:.3f} V",
                    annotation_position="top",
                    annotation_font_size=11,
                    annotation_font_color="#2E86AB"
                )

        # ----- 负电压：直方图 + KDE曲线 + 平均值竖线 -----
        if negative_values:
            fig.add_trace(go.Histogram(
                x=negative_values,
                name='Negative Switch',
                marker_color='#A23B72',
                opacity=0.6,
                histnorm='probability density',
                nbinsx=30,
                legendgroup='Negative',
                showlegend=True
            ))

            if len(negative_values) > 1:
                kde_x = np.linspace(min(negative_values), max(negative_values), 200)
                kde = stats.gaussian_kde(negative_values)
                kde_y = kde(kde_x)
                fig.add_trace(go.Scatter(
                    x=kde_x,
                    y=kde_y,
                    name='Negative Switch (KDE Fit)',
                    line=dict(color='#A23B72', width=2.5),
                    legendgroup='Negative',
                    showlegend=True,
                    mode='lines'
                ))

            if avg_negative is not None:
                fig.add_vline(
                    x=avg_negative,
                    line_width=2,
                    line_dash="dash",
                    line_color="#A23B72",
                    opacity=0.8,
                    annotation_text=f"Avg N: {avg_negative:.3f} V",
                    annotation_position="top",
                    annotation_font_size=11,
                    annotation_font_color="#A23B72"
                )

        # 添加0V参考线
        fig.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="gray", opacity=0.5)

        fig.update_layout(
            title='Switch Voltage Distribution with KDE Fit',
            xaxis_title="Voltage (V)",
            yaxis_title="Density",
            height=500,
            hovermode='closest',
            legend_title="Switch Type",
            barmode='overlay',
            xaxis=dict(
                zeroline=True,
                zerolinewidth=1,
                zerolinecolor='lightgray',
                tickformat='.3f'
            ),
            yaxis=dict(gridcolor='lightgray', zeroline=True, zerolinewidth=1)
        )

        # ========== 显示统计摘要 ==========
        st.markdown("---")
        st.markdown("""
            <style>
                div[data-testid="stMetric"] label {
                    font-size: 12px !important;
                }
                div[data-testid="stMetric"] div {
                    font-size: 18px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🟣 Negative Avg", f"{avg_negative:.4f} V" if avg_negative else "N/A")
        with col2:
            st.metric("🔵 Positive Avg", f"{avg_positive:.4f} V" if avg_positive else "N/A")
        with col3:
            st.metric("📊 Negative Count", f"{len(negative_values)}")
        with col4:
            st.metric("📊 Positive Count", f"{len(positive_values)}")

        # ========== 准备右侧电压点选项 ==========
        positive_stats = filtered_df.groupby('Positive Voltage (V)').agg({
            'Project Name': list,
            'File Name': list,
            'Voltage Condition': list,
            'Negative Voltage (V)': list,
            'N-switch Median (V)': list,
            'P-switch Median (V)': list,
            'N-switch Average (V)': list,
            'P-switch Average (V)': list,
        }).reset_index()
        positive_stats['Type'] = 'Positive Switch'
        positive_stats['Frequency'] = positive_stats['Project Name'].apply(len)
        positive_stats = positive_stats.rename(columns={'Positive Voltage (V)': 'Voltage (V)'})

        negative_stats = filtered_df.groupby('Negative Voltage (V)').agg({
            'Project Name': list,
            'File Name': list,
            'Voltage Condition': list,
            'Positive Voltage (V)': list,
            'N-switch Median (V)': list,
            'P-switch Median (V)': list,
            'N-switch Average (V)': list,
            'P-switch Average (V)': list,
        }).reset_index()
        negative_stats['Type'] = 'Negative Switch'
        negative_stats['Frequency'] = negative_stats['Project Name'].apply(len)
        negative_stats = negative_stats.rename(columns={'Negative Voltage (V)': 'Voltage (V)'})

        plot_df = pd.concat([positive_stats, negative_stats], ignore_index=True)

        # ========== 左右布局 ==========
        left_col, right_col = st.columns([2, 1.5])

        with left_col:
            st.plotly_chart(fig, width='stretch')

        with right_col:
            # 全局样式：下拉选项背景改成浅蓝色，字体保持深色
            st.markdown("""
                <style>
                    /* 下拉框选中项（tag）的背景色 - 浅蓝色，深色字体 */
                    span[data-baseweb="tag"] {
                        background-color: #e6f0ff !important;
                        border-color: #b3d4ff !important;
                        color: #1f1f1f !important;
                    }
                    span[data-baseweb="tag"] span {
                        color: #1f1f1f !important;
                    }
                    span[data-baseweb="tag"] svg {
                        fill: #4a8bbf !important;
                    }
                    /* 下拉框选项字体颜色 - 深色 */
                    div[data-baseweb="select"] li {
                        color: #1f1f1f !important;
                    }
                    div[data-baseweb="select"] div {
                        color: #1f1f1f !important;
                    }
                    /* 下拉框输入框文字颜色 */
                    div[data-baseweb="select"] input {
                        color: #1f1f1f !important;
                    }
                    /* 下拉框占位符文字颜色 */
                    div[data-baseweb="select"] div[data-baseweb="select"] span {
                        color: #666666 !important;
                    }
                    /* 下拉框选项悬停背景 */
                    div[data-baseweb="select"] li:hover {
                        background-color: #f0f5ff !important;
                    }
                    /* 下拉框选中项的高亮背景 */
                    div[data-baseweb="select"] li[aria-selected="true"] {
                        background-color: #e6f0ff !important;
                    }
                    /* 多选下拉框的选中项 */
                    div[data-baseweb="select"] [role="listbox"] div[data-highlighted="true"] {
                        background-color: #e6f0ff !important;
                    }
                    /* 单选下拉框的选中项 */
                    div[data-baseweb="select"] div[role="option"][aria-selected="true"] {
                        background-color: #e6f0ff !important;
                    }
                    /* 所有 select 相关的红色改成浅蓝色 */
                    .stMultiSelect [data-baseweb="tag"] {
                        background-color: #e6f0ff !important;
                    }
                    /* radio 按钮选中时的颜色 */
                    div[role="radiogroup"] input:checked {
                        accent-color: #4a8bbf !important;
                    }
                    /* select 下拉框的整个容器文字颜色 */
                    .stMultiSelect [data-baseweb="select"] * {
                        color: #1f1f1f !important;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.markdown("<h4 style='font-size: 14px; margin-bottom: 10px; margin-top: 0px;'>📋 File Details</h4>",
                        unsafe_allow_html=True)

            # 排序选项
            sort_option = st.radio(
                "Sort by",
                options=["Voltage (Low to High)", "Voltage (High to Low)", "Frequency (Low to High)",
                         "Frequency (High to Low)"],
                horizontal=True,
                label_visibility="collapsed",
                key="tc2_sort_radio"
            )

            # 根据排序选项排序
            if sort_option == "Voltage (Low to High)":
                sorted_df = plot_df.sort_values('Voltage (V)', ascending=True)
            elif sort_option == "Voltage (High to Low)":
                sorted_df = plot_df.sort_values('Voltage (V)', ascending=False)
            elif sort_option == "Frequency (Low to High)":
                sorted_df = plot_df.sort_values('Frequency', ascending=True)
            else:
                sorted_df = plot_df.sort_values('Frequency', ascending=False)

            # 准备下拉框选项
            point_labels = [f"{row['Frequency']} - {row['Voltage (V)']:.3f} V ({row['Type']})"
                            for _, row in sorted_df.iterrows()]

            # 所有选项的索引（默认全选）
            all_indices = list(range(len(point_labels)))

            # 多选下拉框（默认全选）
            selected_indices = st.multiselect(
                "Select voltage points to display",
                options=all_indices,
                format_func=lambda i: point_labels[i],
                default=all_indices,
                placeholder="Select one or more voltage points..."
            )

            st.markdown("---")

            # 根据选中的电压点筛选数据
            if selected_indices:
                selected_voltages_data = [sorted_df.iloc[idx] for idx in selected_indices]

                # 收集所有选中电压点的文件详情
                all_details_data = []
                for selected_row in selected_voltages_data:
                    file_count = len(selected_row['Project Name'])

                    # 添加分隔行
                    all_details_data.append({
                        'Project': f'--- {selected_row["Type"]} @ {selected_row["Voltage (V)"]:.3f} V (Freq: {selected_row["Frequency"]}) ---',
                        'File': '',
                        'Condition': '',
                        'Negative Voltage': '',
                        'Positive Voltage': '',
                        'N Avg (Project)': '',
                        'P Avg (Project)': '',
                        'N Median (Project)': '',
                        'P Median (Project)': '',
                    })

                    for i in range(file_count):
                        project = selected_row['Project Name'][i]
                        file_name = selected_row['File Name'][i]
                        voltage_condition = selected_row['Voltage Condition'][i]

                        if selected_row['Type'] == 'Positive Switch':
                            other_voltage = selected_row['Negative Voltage (V)'][i]
                            pos_voltage = selected_row['Voltage (V)']
                            neg_voltage = other_voltage
                        else:
                            other_voltage = selected_row['Positive Voltage (V)'][i]
                            pos_voltage = other_voltage
                            neg_voltage = selected_row['Voltage (V)']

                        n_median = selected_row['N-switch Median (V)'][i] if isinstance(
                            selected_row['N-switch Median (V)'], list) else selected_row['N-switch Median (V)']
                        p_median = selected_row['P-switch Median (V)'][i] if isinstance(
                            selected_row['P-switch Median (V)'], list) else selected_row['P-switch Median (V)']
                        n_avg = selected_row['N-switch Average (V)'][i] if isinstance(
                            selected_row['N-switch Average (V)'], list) else selected_row['N-switch Average (V)']
                        p_avg = selected_row['P-switch Average (V)'][i] if isinstance(
                            selected_row['P-switch Average (V)'], list) else selected_row['P-switch Average (V)']

                        def fmt_voltage(val):
                            if pd.isna(val):
                                return 'N/A'
                            try:
                                return f"{float(val):.3f} V"
                            except:
                                return str(val)

                        def fmt_value(val):
                            if pd.isna(val) or val == 'N/A':
                                return 'N/A'
                            try:
                                return f"{float(val):.3f} V"
                            except:
                                return str(val)

                        all_details_data.append({
                            'Project': project,
                            'File': file_name,
                            'Condition': voltage_condition,
                            'Positive Voltage': fmt_voltage(pos_voltage),
                            'Negative Voltage': fmt_voltage(neg_voltage),
                            'N Avg (Project)': fmt_value(n_avg),
                            'P Avg (Project)': fmt_value(p_avg),
                            'N Median (Project)': fmt_value(n_median),
                            'P Median (Project)': fmt_value(p_median),
                        })

                details_df = pd.DataFrame(all_details_data)
                st.markdown(
                    f"**{len(selected_indices)} voltage point(s) selected, {len(details_df) - len(selected_indices)} files shown**")
                st.dataframe(details_df, width='stretch', height=500)
            else:
                st.info("No voltage points selected. Please select at least one point above.")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Please check data format in CSV files")