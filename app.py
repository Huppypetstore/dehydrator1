import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Dict

# Define constants for the categories
MAIN_CATEGORIES = [
    "エネルギー関連", "クリーニング工場", "下水関連",
    "化学製品工場", "化学薬品工場", "機械製造業", "産業廃棄物", "商業施設",
    "食品製造", "製紙", "繊維製品", "畜産", "発電所", "公共下水"
]

SUB_CATEGORIES = [
    "ガラス", "ごみ処理施設", "シャーペンの芯製造工場", "ショッピングモール",
    "し尿処理場", "バイオガス", "バイオマス", "ビル", "ホテル",
    "メタン発酵残渣", "レジャー施設", "レンダリング", "移動脱水車", "飲料",
    "下水処理場", "化粧品", "外食", "学校", "給食センター", "漁業集落排水",
    "金属", "健康食品", "自動車・二輪", "樹脂", "浄化槽", "食肉加工",
    "食品加工", "食料品", "水産加工", "精米", "製パン", "製菓",
    "製麵", "製薬", "洗剤", "染料", "繊維・衣料", "繊維製品", "調味料",
    "漬物", "電気・電子部品", "電力", "塗装", "塗装系排水処理", "塗料",
    "肉牛", "乳牛（酪农）", "农业集落排水",
    "廃プラ", "プラ再生工場", "発電所", "病院", "药品", "油田", "溶剂",
    "养鸡", "养猪", "冷凍・チルド・中食", "OD直脱"
]

DEWATERING_MACHINE_TYPES = [
    "多重円板型脱水機", "多重板型スクリュープレス脱水機", "多重板型スクリュープレス脱水機小規模下水"
]

def load_and_process_data(uploaded_file) -> pd.DataFrame:
    """Load and process the uploaded Excel file."""
    try:
        df = pd.read_excel(uploaded_file)

        # Data Cleaning: Convert non-numeric, empty strings, or whitespace to NaN for specific columns
        columns_to_clean = ['固形物回収率 %', '脱水ケーキ含水率 %']
        for col in columns_to_clean:
            if col in df.columns:
                # Convert all non-numeric values (including blank strings) to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Also replace any remaining whitespace-only strings with NaN
                df[col] = df[col].replace(r'^s*$', pd.NA, regex=True)

        return df
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return None

def create_boxplot(df: pd.DataFrame, value_col: str, category_col: str, show_outliers: bool = True) -> None:
    """Create and display a boxplot for the specified value column, grouped by a specified category.
       Optionally hide outliers."""
    if df is not None and not df.empty:
        points_mode = 'all' if show_outliers else False
        fig = px.box(
            df,
            x=category_col,
            y=value_col,
            points=points_mode,
            title=f"{category_col}ごとの{value_col}の箱ひげ図"
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

def create_summary_chart(df: pd.DataFrame, group_by: str) -> None:
    """Create and display a bar chart for the specified grouping (count)."""
    if df is not None and not df.empty:
        # Group by the primary category and then by '脱水機種別' for color splitting
        if group_by in ["業種大分類", "業種中分類"]:
            # Use the dataframe filtered by user selections in main directly
            df_to_chart = df

            # Group the filtered dataframe
            # Ensure '脱水機種別' column exists before grouping
            if '脱水機種別' in df_to_chart.columns:
                 summary = df_to_chart.groupby([group_by, '脱水機種別']).size().reset_index(name='件数')
                 # Sort by primary group and then by count for stacking order
                 summary = summary.sort_values(by=[group_by, '件数'], ascending=[True, False])
                 color_col = '脱水機種別'
            else:
                 # Fallback if '脱水機種別' column is missing in the filtered data
                 summary = df_to_chart.groupby([group_by]).size().reset_index(name='件数')
                 color_col = None


        else:
            summary = df[group_by].value_counts().reset_index()
            summary.columns = [group_by, '件数']
            color_col = None # No color grouping for other chart types

        # Calculate total counts for sorting x-axis categories
        # Use the original df for sorting to get all categories, or the summary df if only filtered categories are desired
        # Using summary df for sorting categories present in the current view
        if group_by in summary.columns:
             total_counts = summary.groupby(group_by)['件数'].sum().reset_index()
             sorted_categories = total_counts.sort_values('件数', ascending=False)[group_by].tolist()
        else:
             # Fallback sorting if group_by column is not directly in summary (e.g., if no data after filtering)
             sorted_categories = summary[group_by].tolist() if group_by in summary.columns else []


        fig = px.bar(
            summary,
            x=group_by,
            y='件数',
            title=f'{group_by}別の件数',
            labels={group_by: '', '件数': '件数'},
            color=color_col, # Apply color grouping
            text='件数', # Use the '件数' column for text labels
            text_auto=True # Automatically position text labels
        ,
            color_discrete_sequence=px.colors.qualitative.Pastel # Use a pastel color sequence
        ,
            category_orders={group_by: sorted_categories} # Apply sorting to x-axis categories
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="引き合い情報分析 APP", layout="wide")
    st.title("📊 引き合い情報分析 APP")

    # ファイルアップロード
    uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=['xlsx', 'xls'])

    if uploaded_file is not None:
        df = load_and_process_data(uploaded_file)

        if df is not None:
            # フィルター設定
            st.header("フィルター設定")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                order_status = st.multiselect(
                    "受注の有無",
                    options=[True, False],
                    default=[True, False]
                )
            with col2:
                # Use predefined list for options
                selected_main_categories = st.multiselect(
                    "業種大分類",
                    options=sorted(MAIN_CATEGORIES), # Use the constant list directly
                    default=[]
                )
            with col3:
                # Use predefined list for options
                selected_sub_categories = st.multiselect(
                    "業種中分類",
                    options=sorted(SUB_CATEGORIES), # Use the constant list directly
                    default=[]
                )
            with col4:
                selected_machine_types = st.multiselect(
                    "脱水機種別",
                    options=DEWATERING_MACHINE_TYPES,
                    default=[]
                )

            filtered_df = df.copy()
            if order_status:
                filtered_df = filtered_df[filtered_df['受注の有無'].isin(order_status)]
            if selected_main_categories:
                # Ensure the column exists before filtering
                if '業種大分類' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['業種大分類'].isin(selected_main_categories)]
                else:
                    st.warning("データに「業種大分類」列が見つかりませんでした。")
                    filtered_df = filtered_df[filtered_df['業種大分類'].isnull()] # Filter out everything


            if selected_sub_categories:
                # Ensure the column exists before filtering
                if '業種中分類' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['業種中分類'].isin(selected_sub_categories)]
                else:
                    st.warning("データに「業種中分類」列が見つかりませんでした。")
                    filtered_df = filtered_df[filtered_df['業種中分類'].isnull()] # Filter out everything


            if selected_machine_types and '脱水機種別' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['脱水機種別'].isin(selected_machine_types)]
            # Add handling for when '脱水機種別' column is missing but a selection was made
            elif selected_machine_types and '脱水機種別' not in filtered_df.columns:
                 st.warning("データに「脱水機種別」列が見つかりませんでした。脱水機種別フィルターは適用されません。")
                 # In this case, the filter is effectively ignored, no need to modify filtered_df


            # 分析結果（件数）
            st.header("分析結果")
            st.write(f"フィルター適用後の総件数: {len(filtered_df)}")

            st.subheader("件数グラフ")
            chart_type = st.radio(
                "グラフの種類を選択してください:",
                ["業種大分類", "業種中分類", "受注の有無"]
            )
            # Ensure the selected chart_type column exists in the dataframe before charting
            if chart_type in filtered_df.columns:
                create_summary_chart(filtered_df, chart_type)
            else:
                st.warning(f"データに「{chart_type}」列が見つかりませんでした。件数グラフは表示されません。")


            # 数値分析（箱ひげ図と要約統計量）
            st.header("数値分析（箱ひげ図と要約統計量）")
            # Use the filtered dataframe to get numeric columns
            numeric_columns = filtered_df.select_dtypes(include='number').columns.tolist()

            # Initialize selected value variables
            value_col_main = None
            value_col_sub = None

            if numeric_columns:
                # 2つの列を作成して箱ひげ図と要約統計量を並列配置
                col_box1, col_box2 = st.columns(2)

                with col_box1:
                    # 箱ひげ図 1：業種大分類 ごと
                    st.subheader("箱ひげ図 1：業種大分類")
                    value_col_main = st.selectbox("数値項目を選択してください", numeric_columns, key="boxplot1_value")
                    show_outliers_main = st.checkbox("外れ値を表示", value=False, key="outliers_main")
                    show_zeros_main = st.checkbox("0を表示", value=False, key="show_zeros_main")
                    # Ensure '業種大分類' column exists before creating the boxplot
                    if '業種大分類' in filtered_df.columns:
                        if value_col_main:
                            # Filter out 0 and NaN values for specific columns if selected
                            df_for_analysis_main = filtered_df.copy()
                            columns_to_filter_zero_and_nan = ['固形物回収率 %', '脱水ケーキ含水率 %']
                            if value_col_main in columns_to_filter_zero_and_nan and not show_zeros_main:
                                df_for_analysis_main = df_for_analysis_main[df_for_analysis_main[value_col_main].notna() & (df_for_analysis_main[value_col_main] != 0)]
                            elif value_col_main in columns_to_filter_zero_and_nan and show_zeros_main:
                                df_for_analysis_main = df_for_analysis_main[df_for_analysis_main[value_col_main].notna()] # Just filter NaNs if show_zeros is true


                            # Sort categories by count for boxplot
                            # Use the filtered dataframe for counts to reflect the current view
                            category_counts_main = df_for_analysis_main["業種大分類"].value_counts().reset_index()
                            category_counts_main.columns = ["業種大分類", 'count']
                            sorted_categories_main = category_counts_main.sort_values('count', ascending=False)["業種大分類"].tolist()

                            # Create boxplot with sorted categories
                            fig_main = px.box(
                                df_for_analysis_main,
                                x="業種大分類",
                                y=value_col_main,
                                points='all' if show_outliers_main else False,
                                title=f"業種大分類ごとの{value_col_main}の箱ひげ図",
                                category_orders={"業種大分類": sorted_categories_main}
                            )
                            fig_main.update_layout(
                                xaxis_tickangle=-45,
                                height=600
                            )
                            st.plotly_chart(fig_main, use_container_width=True, config={'scrollZoom': True})

                            st.markdown("---") # 区切り線を追加

                            # 要約統計量：業種大分類ごと
                            st.subheader(f"📊 {value_col_main} の要約統計量 (業種大分類別)")
                            try:
                                # Ensure the column exists before grouping
                                if '業種大分類' in df_for_analysis_main.columns:
                                     grouped_stats_main = df_for_analysis_main.groupby("業種大分類")[value_col_main].describe()
                                     st.dataframe(grouped_stats_main)
                                else:
                                     st.warning("データに「業種大分類」列が見つからなかったため、業種大分類別の要約統計量は表示されません。")

                            except Exception as e:
                                st.error(f"業種大分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                    else:
                         st.warning("データに「業種大分類」列が見つからなかったため、箱ひげ図 1 は表示されません。")


                with col_box2:
                    # 箱ひげ図 2：業種中分類 ごと
                    st.subheader("箱ひげ図 2：業種中分類")
                    value_col_sub = st.selectbox("数値項目を選択してください", numeric_columns, key="boxplot2_value")
                    show_outliers_sub = st.checkbox("外れ値を表示", value=False, key="outliers_sub")
                    show_zeros_sub = st.checkbox("0を表示", value=False, key="show_zeros_sub")
                    # Ensure '業種中分類' column exists before creating the boxplot
                    if '業種中分類' in filtered_df.columns:
                        if value_col_sub:
                            # Filter out 0 and NaN values for specific columns if selected
                            df_for_analysis_sub = filtered_df.copy()
                            columns_to_filter_zero_and_nan = ['固形物回収率 %', '脱水ケーキ含水率 %']
                            if value_col_sub in columns_to_filter_zero_and_nan and not show_zeros_sub:
                                df_for_analysis_sub = df_for_analysis_sub[df_for_analysis_sub[value_col_sub].notna() & (df_for_analysis_sub[value_col_sub] != 0)]
                            elif value_col_sub in columns_to_filter_zero_and_nan and show_zeros_sub:
                                df_for_analysis_sub = df_for_analysis_sub[df_for_analysis_sub[value_col_sub].notna()] # Just filter NaNs if show_zeros is true


                            # Sort categories by count for boxplot
                            # Use the filtered dataframe for counts to reflect the current view
                            category_counts_sub = df_for_analysis_sub["業種中分類"].value_counts().reset_index()
                            category_counts_sub.columns = ["業種中分類", 'count']
                            sorted_categories_sub = category_counts_sub.sort_values('count', ascending=False)["業種中分類"].tolist()


                            # Create boxplot with sorted categories
                            fig_sub = px.box(
                                df_for_analysis_sub,
                                x="業種中分類",
                                y=value_col_sub,
                                points='all' if show_outliers_sub else False,
                                title=f"業種中分類ごとの{value_col_sub}の箱ひげ図",
                                category_orders={"業種中分類": sorted_categories_sub}
                            )
                            fig_sub.update_layout(
                                xaxis_tickangle=-45,
                                height=600
                            )
                            st.plotly_chart(fig_sub, use_container_width=True, config={'scrollZoom': True})

                            st.markdown("---") # 区切り線を追加

                            # 要約統計量：業種中分類ごと
                            st.subheader(f"📊 {value_col_sub} の要約統計量 (業種中分類別)")
                            try:
                                # Ensure the column exists before grouping
                                if '業種中分類' in df_for_analysis_sub.columns:
                                     grouped_stats_sub = df_for_analysis_sub.groupby("業種中分類")[value_col_sub].describe()
                                     st.dataframe(grouped_stats_sub)
                                else:
                                     st.warning("データに「業種中分類」列が見つからなかったため、業種中分類別の要約統計量は表示されません。")

                            except Exception as e:
                                st.error(f"業種中分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                    else:
                         st.warning("データに「業種中分類」列が見つからなかったため、箱ひげ図 2 は表示されません。")


            else:
                st.warning("箱ひげ図と要約統計量を作成できる数値項目が見つかりません。")

            # フィルター後のデータ
            st.header("フィルター後のデータ")
            st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
