import streamlit as st
import pandas as pd
import plotly.express as px
import os


def show():
    # 删除标题，直接开始

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

        # 读取分组汇总数据
        n_median_map = {}
        p_median_map = {}

        if os.path.exists(summary_csv_path):
            df_summary = pd.read_csv(summary_csv_path, encoding='utf-8')
            df_summary.columns = df_summary.columns.str.strip().str.replace('\ufeff', '')
            df_summary = df_summary.rename(columns={
                '所属项目': 'Project Name',
                '电压条件': 'Voltage Condition',
                'N-switch中位数(V)': 'N-switch Median (V)',
                'P-switch中位数(V)': 'P-switch Median (V)',
            })
            # 创建映射
            for _, row in df_summary.iterrows():
                key = f"{row['Project Name']}|{row['Voltage Condition']}"
                n_median_map[key] = row.get('N-switch Median (V)', 'N/A')
                p_median_map[key] = row.get('P-switch Median (V)', 'N/A')

        # 重命名主数据的列
        df = df.rename(columns={
            '所属项目': 'Project Name',
            '电压条件': 'Voltage Condition',
            '正切换电压(V)': 'Positive Voltage (V)',
            '负切换电压(V)': 'Negative Voltage (V)',
            '文件名': 'File Name',
        })

        # 添加中位数列
        df['Match Key'] = df['Project Name'] + '|' + df['Voltage Condition']
        df['N-switch Median (V)'] = df['Match Key'].map(n_median_map)
        df['P-switch Median (V)'] = df['Match Key'].map(p_median_map)

        # ========== 筛选器（默认全选） ==========
        voltage_options = sorted(df['Voltage Condition'].dropna().unique().tolist())
        selected_voltages = st.multiselect(
            "Filter by Voltage Condition",
            options=voltage_options,
            default=voltage_options,
            placeholder="Select voltage conditions..."
        )

        # 应用筛选
        filtered_df = df.copy()
        if selected_voltages:
            filtered_df = filtered_df[filtered_df['Voltage Condition'].isin(selected_voltages)]

        if len(filtered_df) == 0:
            st.warning("No data available")
            return

        # ========== 统计频次数据（Y轴 = 数量） ==========
        # 正电压频次统计
        positive_stats = filtered_df.groupby('Positive Voltage (V)').agg({
            'Project Name': list,
            'File Name': list,
            'Voltage Condition': list,
            'Negative Voltage (V)': list,
            'N-switch Median (V)': list,
            'P-switch Median (V)': list,
        }).reset_index()
        positive_stats['Type'] = 'Positive Switch'
        positive_stats['Frequency'] = positive_stats['Project Name'].apply(len)
        positive_stats = positive_stats.rename(columns={'Positive Voltage (V)': 'Voltage (V)'})

        # 负电压频次统计
        negative_stats = filtered_df.groupby('Negative Voltage (V)').agg({
            'Project Name': list,
            'File Name': list,
            'Voltage Condition': list,
            'Positive Voltage (V)': list,
            'N-switch Median (V)': list,
            'P-switch Median (V)': list,
        }).reset_index()
        negative_stats['Type'] = 'Negative Switch'
        negative_stats['Frequency'] = negative_stats['Project Name'].apply(len)
        negative_stats = negative_stats.rename(columns={'Negative Voltage (V)': 'Voltage (V)'})

        # 合并
        plot_df = pd.concat([positive_stats, negative_stats], ignore_index=True)

        # ========== 创建散点图（Y轴 = 频次） ==========
        fig = px.scatter(
            plot_df,
            x='Voltage (V)',
            y='Frequency',
            color='Type',
            title='Positive vs Negative Switch Voltage Distribution',
            labels={'Voltage (V)': 'Voltage (V)', 'Frequency': 'Frequency'},
            color_discrete_map={'Positive Switch': '#2E86AB', 'Negative Switch': '#A23B72'},
        )

        # 统一点的大小
        fig.update_traces(
            marker=dict(size=12, opacity=0.7, line=dict(width=1, color='white')),
            hovertemplate="<b>Voltage: %{x:.3f} V</b><br>Frequency: %{y}<br>Type: %{customdata}<extra></extra>"
        )
        fig.update_traces(customdata=plot_df['Type'].values)

        # 添加0V参考线
        fig.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="gray", opacity=0.7)

        # 更新布局
        fig.update_layout(
            xaxis_title="Voltage (V)",
            yaxis_title="Frequency",
            height=500,
            hovermode='closest',
            legend_title="Switch Type",
            xaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor='lightgray'),
            yaxis=dict(gridcolor='lightgray', zeroline=True, zerolinewidth=1)
        )

        # ========== 左右布局：左边图表，右边详情 ==========
        left_col, right_col = st.columns([2, 1.5])

        with left_col:
            # 显示图表
            st.plotly_chart(fig, width='stretch')

        with right_col:
            # 减小右侧边距
            st.markdown("<style>div[data-testid='column']:nth-child(2) {padding-left: 0px !important;}</style>",
                        unsafe_allow_html=True)

            # File Details 标题
            st.markdown("<h4 style='font-size: 14px; margin-bottom: 10px; margin-top: 0px;'>📋 File Details</h4>",
                        unsafe_allow_html=True)

            # ========== 排序选项 ==========
            # 添加唯一的 key 解决 radio 冲突
            sort_option = st.radio(
                "Sort by",
                options=["Voltage (Low to High)", "Voltage (High to Low)", "Frequency (Low to High)", "Frequency (High to Low)"],
                horizontal=True,
                label_visibility="collapsed",
                key="tc2_sort_radio"  # 添加唯一的 key
            )

            # 根据排序选项对 plot_df 进行排序
            if sort_option == "Voltage (Low to High)":
                sorted_df = plot_df.sort_values('Voltage (V)', ascending=True)
            elif sort_option == "Voltage (High to Low)":
                sorted_df = plot_df.sort_values('Voltage (V)', ascending=False)
            elif sort_option == "Frequency (Low to High)":
                sorted_df = plot_df.sort_values('Frequency', ascending=True)
            else:  # Frequency (High to Low)
                sorted_df = plot_df.sort_values('Frequency', ascending=False)

            # 下拉选择框（频次放在最前面）
            point_labels = [f"{row['Frequency']} - {row['Voltage (V)']:.3f} V ({row['Type']})"
                            for _, row in sorted_df.iterrows()]

            selected_idx = st.selectbox(
                "Select a point",
                options=range(len(point_labels)),
                format_func=lambda i: point_labels[i],
                label_visibility="collapsed"
            )

            selected_row = sorted_df.iloc[selected_idx]

            # 基本信息（字体调大）
            st.markdown(
                f"<p style='font-size: 15px; margin-bottom: 8px;'><b>Voltage:</b> {selected_row['Voltage (V)']:.3f} V</p>",
                unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 15px; margin-bottom: 8px;'><b>Type:</b> {selected_row['Type']}</p>",
                        unsafe_allow_html=True)
            st.markdown(
                f"<p style='font-size: 15px; margin-bottom: 12px;'><b>Frequency:</b> {selected_row['Frequency']}</p>",
                unsafe_allow_html=True)

            st.divider()

            # 构建详细信息表格
            details_data = []
            file_count = len(selected_row['Project Name'])

            for i in range(file_count):
                project = selected_row['Project Name'][i]
                file_name = selected_row['File Name'][i]
                voltage_condition = selected_row['Voltage Condition'][i]

                # 获取对应的另一极电压
                if selected_row['Type'] == 'Positive Switch':
                    other_voltage = selected_row['Negative Voltage (V)'][i]
                    other_label = 'Negative Voltage'
                else:
                    other_voltage = selected_row['Positive Voltage (V)'][i]
                    other_label = 'Positive Voltage'

                # 获取中位数（项目的中位数）
                n_median = selected_row['N-switch Median (V)'][i] if isinstance(selected_row['N-switch Median (V)'],
                                                                                list) else selected_row[
                    'N-switch Median (V)']
                p_median = selected_row['P-switch Median (V)'][i] if isinstance(selected_row['P-switch Median (V)'],
                                                                                list) else selected_row[
                    'P-switch Median (V)']

                def fmt_median(val):
                    if pd.isna(val) or val == 'N/A':
                        return 'N/A'
                    try:
                        return f"{float(val):.3f} V"
                    except:
                        return str(val)

                details_data.append({
                    'Project': project,
                    'File': file_name,
                    'Condition': voltage_condition,
                    other_label: f"{other_voltage:.3f} V" if isinstance(other_voltage, (int, float)) else str(
                        other_voltage),
                    'N Median (Project)': fmt_median(n_median),
                    'P Median (Project)': fmt_median(p_median),
                })

            details_df = pd.DataFrame(details_data)
            st.dataframe(details_df, width='stretch', height=400)

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Please check data format in CSV files")