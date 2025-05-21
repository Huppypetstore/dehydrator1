import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Dict

# Define constants for the categories
MAIN_CATEGORIES = [
    "エネルギー関連", "クリーニング工場", "レンタル機として保有", "運送業", "下水関連",
    "化学製品工場", "化学薬品工場", "機械製造業", "工業", "産業廃棄物", "商業施設",
    "食品製造", "生コン", "製紙", "繊維製品", "畜産", "発電所"
]

SUB_CATEGORIES = [
    "ガラス", "ごみ処理施設", "ゴム製品", "シャーペンの芯製造工場", "ショッピングモール",
    "し尿処理場", "その他", "バイオガス", "バイオマス", "ビル", "ホテル",
    "メタン発酵残渣", "レジャー施設", "レンダリング", "移動脱水車", "飲料",
    "下水処理場", "化粧品", "外食", "学校", "給食センター", "漁業集落排水",
    "金属", "健康食品", "自動車・二輪", "樹脂", "浄化槽", "食肉加工",
    "食品加工", "食料品", "飲料", "水産加工", "精米", "製パン", "製菓",
    "製麵", "製薬", "洗剤", "染料", "繊維・衣料", "繊維製品", "調味料",
    "漬物", "電気・電子部品", "電力", "塗装", "塗装系排水処理", "塗料",
    "肉牛", "乳飲料", "乳牛（酪農）", "乳製品", "農業集落排水", "農業⇒公共下水",
    "廃プラ", "プラ再生工場", "発電所", "病院", "薬品", "油田", "溶剤",
    "養鶏", "養豚", "冷凍・チルド・中食"
]

DEWATERING_MACHINE_TYPES = [
    "多重円板型脱水機", "多重板型スクリュープレス脱水機"
]

def load_and_process_data(uploaded_file) -> pd.DataFrame:
    """Load and process the uploaded Excel file."""
    try:
        df = pd.read_excel(uploaded_file)

        # Data Cleaning based on the provided snippet:
        # Convert specific columns to numeric, coercing errors and replacing whitespace-only strings with NaN
        columns_to_clean = ['固形物回収率 %', '脱水ケーキ含水率 %']
        for col in columns_to_clean:
            if col in df.columns:
                # Convert all non-numeric values (including blank strings that are not just whitespace) to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Also replace any remaining whitespace-only strings with NaN (apply after to_numeric)
                # Ensure the column is string type before applying regex replace
                df[col] = df[col].astype(str).replace(r'^\s*$', pd.NA, regex=True)

        return df
    except Exception as e:
        st.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
        return None

def create_boxplot(df: pd.DataFrame, value_col: str, category_col: str, show_outliers: bool = True) -> None:
    """Create and display a boxplot for the specified value column, grouped by a specified category.
       Optionally hide outliers."""
    # Ensure the necessary columns exist and dataframe is not empty
    if df is not None and not df.empty and category_col in df.columns and value_col in df.columns:
        # Drop rows where the category column or value column is NaN for plotting
        df_plot = df.dropna(subset=[category_col, value_col]).copy()

        if df_plot.empty:
             st.warning(f"箱ひげ図を作成するための有効なデータがありません。選択された列 ('{category_col}', '{value_col}') の値がすべて欠損値であるか、フィルターによってデータがなくなりました。")
             return

        points_mode = 'all' if show_outliers else False

        # Sort categories by count for boxplot consistency
        try:
            category_counts = df_plot[category_col].value_counts().reset_index()
            category_counts.columns = [category_col, 'count']
            sorted_categories = category_counts.sort_values('count', ascending=False)[category_col].tolist()

            # Check if there are enough categories and data points to create a meaningful boxplot
            if len(sorted_categories) < 2 or df_plot[value_col].nunique() < 2:
                 st.warning(f"選択された列 ('{category_col}', '{value_col}') には、箱ひげ図を作成するための十分なカテゴリまたは数値のバリエーションがありません。")
                 return # Exit if not enough variation for a boxplot


            fig = px.box(
                df_plot,
                x=category_col,
                y=value_col,
                points=points_mode,
                title=f"{category_col}ごとの{value_col}の箱ひげ図",
                category_orders={category_col: sorted_categories} # Apply sorting
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                height=600
            )
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

        except Exception as e:
             st.error(f"箱ひげ図の作成中にエラーが発生しました: {str(e)}")
             st.warning("箱ひげ図の作成中に問題が発生しました。データ形式または列名を確認してください。")


    elif df is not None and df.empty:
         st.warning("箱ひげ図を作成するためのデータがありません。")
    elif df is None:
         st.warning("データがロードされていません。")
    else:
         st.warning(f"箱ひげ図の作成に必要な列 ('{category_col}' または '{value_col}') がデータに存在しません。")


def create_summary_chart(df: pd.DataFrame, group_by: str) -> None:
    """Create and display a bar chart for the specified grouping (count)."""
    # Ensure the necessary column exists and dataframe is not empty
    if df is not None and not df.empty and group_by in df.columns:
         # Ensure the group_by column is not entirely NA after filtering
        if df[group_by].dropna().empty:
             st.warning(f"件数グラフを作成するための有効なデータがありません。選択されたグループ項目 '{group_by}' の値がすべて欠損値であるか、フィルターによってデータがなくなりました。")
             return

        # Group by the primary category and then by '脱水機種別' for color splitting (as in the snippet)
        # Check if '脱水機種別' column exists before attempting to group by it
        if group_by in ["業種大分類", "業種中分類"] and '脱水機種別' in df.columns:
            allowed_machine_types = ["多重円板型脱水機", "多重板型スクリュープレス脱水機"]
            # Filter the dataframe before grouping
            df_to_chart = df[df['脱水機種別'].isin(allowed_machine_types)]

            # Group the filtered dataframe
            if not df_to_chart.empty:
                # Handle potential NaN values in group_by or '脱水機種別' before size()
                summary = df_to_chart.groupby([group_by, '脱水機種別'], dropna=False).size().reset_index(name='件数')
                # Sort by primary group and then by count for stacking order
                summary = summary.sort_values(by=[group_by, '件数'], ascending=[True, False])
                color_col = '脱水機種別'
            else:
                st.warning(f"選択された脱水機種別 ('{allowed_machine_types}') に一致するデータがないため、件数グラフを作成できません。")
                return # Exit if no data matches the machine types
        else:
            # Handle other grouping types or cases where '脱水機種別' is missing
            # Handle potential NaN values in group_by before value_counts()
            if df[group_by].hasnans:
                summary = df[group_by].value_counts(dropna=False).reset_index()
                summary.columns = [group_by, '件数']
                # Rename NaN index to something descriptive if needed for display
                summary[group_by] = summary[group_by].fillna("不明/欠損値")
            else:
                summary = df[group_by].value_counts().reset_index()
                summary.columns = [group_by, '件数']

            color_col = None # No color grouping for other chart types

        # Check if summary is empty after grouping
        if summary.empty:
             st.warning(f"選択されたグループ項目 '{group_by}' に基づいてグラフを作成できません。")
             return

        # Calculate total counts for sorting x-axis categories
        # Ensure group_by column in summary does not contain unhashable types if any NaNs were filled
        summary[group_by] = summary[group_by].astype(str)
        total_counts = summary.groupby(group_by)['件数'].sum().reset_index()
        sorted_categories = total_counts.sort_values('件数', ascending=False)[group_by].tolist()


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
    elif df is not None and df.empty:
         st.warning(f"件数グラフを作成するためのデータがありません。フィルターによってデータがなくなりました。")
    elif df is None:
         st.warning("データがロードされていません。")
    else:
         st.warning(f"件数グラフの作成に必要な列 ('{group_by}') がデータに存在しません。")


def main():
    st.set_page_config(page_title="引き合い情報分析 APP", layout="wide")
    st.title("📊 引き合い情報分析 APP")

    # ファイルアップロード
    uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=['xlsx', 'xls'])

    df = None # Initialize df outside the if block

    if uploaded_file is not None:
        df = load_and_process_data(uploaded_file)

    # Proceed only if data is loaded
    if df is not None and not df.empty:

        # フィルター設定 (Initial Filters based on the provided snippet)
        st.header("フィルター設定")
        col1, col2, col3, col4 = st.columns(4)

        # Get options directly from the loaded dataframe for filtering
        order_status_options = df['受注の有無'].unique().tolist() if '受注の有無' in df.columns else []
        main_categories_options = df['業種大分類'].unique().tolist() if '業種大分類' in df.columns else []
        sub_categories_options = df['業種中分類'].unique().tolist() if '業種中分類' in df.columns else []
        machine_types_options = df['脱水機種別'].unique().tolist() if '脱水機種別' in df.columns else []


        with col1:
            if '受注の有無' in df.columns:
                # Filter out potential NaN/None for display in multiselect
                selectable_order_status_options = [x for x in order_status_options if pd.notna(x)]
                # Offer True/False if they exist in the data
                options_for_multiselect = []
                if True in selectable_order_status_options: options_for_multiselect.append(True)
                if False in selectable_order_status_options: options_for_multiselect.append(False)

                # If there are no True/False values, just show a warning and skip filter
                if options_for_multiselect:
                    order_status = st.multiselect(
                        "受注の有無",
                        options=options_for_multiselect,
                        default=options_for_multiselect # Default to all available T/F options
                    )
                else:
                    st.warning("列 '受注の有無' に True/False 値が見つかりません。フィルターは適用されません。")
                    order_status = None # No options means no filter applied

            else:
                st.warning("列 '受注の有無' がデータに存在しません。フィルターは適用されません。")
                order_status = None


        with col2:
            if '業種大分類' in df.columns:
                # Remove NaN from options for display
                main_categories_options_cleaned = [x for x in main_categories_options if pd.notna(x)]
                selected_main_categories = st.multiselect(
                    "業種大分類",
                    options=main_categories_options_cleaned,
                    default=[]
                )
            else:
                st.warning("列 '業種大分類' がデータに存在しません。フィルターは適用されません。")
                selected_main_categories = None


        with col3:
             if '業種中分類' in df.columns:
                 # Remove NaN from options for display
                 sub_categories_options_cleaned = [x for x in sub_categories_options if pd.notna(x)]
                 selected_sub_categories = st.multiselect(
                    "業種中分類",
                    options=sub_categories_options_cleaned,
                    default=[]
                 )
             else:
                 st.warning("列 '業種中分類' がデータに存在しません。フィルターは適用されません。")
                 selected_sub_categories = None

        with col4:
            if '脱水機種別' in df.columns:
                # Remove NaN from options for display
                machine_types_options_cleaned = [x for x in machine_types_options if pd.notna(x)]
                selected_machine_types = st.multiselect(
                    "脱水機種別",
                    options=machine_types_options_cleaned,
                    default=[]
                )
            else:
                 st.warning("列 '脱水機種別' がデータに存在しません。フィルターは適用されません。")
                 selected_machine_types = None


        # Apply filters from multiselects to create filtered_df
        filtered_df = df.copy()
        if order_status is not None and order_status and '受注の有無' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['受注の有無'].isin(order_status)]
        if selected_main_categories is not None and selected_main_categories and '業種大分類' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['業種大分類'].isin(selected_main_categories)]
        if selected_sub_categories is not None and selected_sub_categories and '業種中分類' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['業種中分類'].isin(selected_sub_categories)]

        # Apply machine type filter only if column exists and selections were made
        if selected_machine_types is not None and selected_machine_types and '脱水機種別' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['脱水機種別'].isin(selected_machine_types)]


        # --- 分析結果 (Analysis Results based on the provided snippet) ---
        st.header("分析結果")
        st.write(f"フィルター適用後の総件数: {len(filtered_df)}")

        if not filtered_df.empty: # Only show charts/stats if filtered data is not empty

            # 件数グラフ (Summary Chart)
            st.subheader("件数グラフ")
            # Only show chart options if the corresponding columns exist and have non-NaN values in filtered_df
            chart_options = []
            if '業種大分類' in filtered_df.columns and not filtered_df['業種大分類'].dropna().empty:
                chart_options.append("業種大分類")
            if '業種中分類' in filtered_df.columns and not filtered_df['業種中分類'].dropna().empty:
                chart_options.append("業種中分類")
            if '受注の有無' in filtered_df.columns and not filtered_df['受注の有無'].dropna().empty:
                chart_options.append("受注の有無")
            # Check for '脱水機種別' as it's used for coloring in some summary charts
            if '脱水機種別' not in filtered_df.columns:
                 st.warning("列 '脱水機種別' がデータに存在しないため、業種別の件数グラフは単色になります。")


            if chart_options:
                 chart_type = st.radio(
                    "グラフの種類を選択してください:",
                    chart_options,
                    key="summary_chart_type" # Added a key
                 )
                 create_summary_chart(filtered_df, chart_type)
            else:
                 st.warning("件数グラフを作成できる有効なデータを含む列が見つかりません ('業種大分類', '業種中分類', '受注の有無')")


            # 数値分析（箱ひげ図と要約統計量）(Numerical Analysis)
            st.subheader("数値分析（箱ひげ図と要約統計量）")
            # Get numeric columns from the filtered data
            numeric_columns = filtered_df.select_dtypes(include='number').columns.tolist()

            # Ensure there are numeric columns and category columns for plotting
            if numeric_columns and ('業種大分類' in filtered_df.columns or '業種中分類' in filtered_df.columns):

                # 2つの列を作成して箱ひげ図と要約統計量を並列配置
                col_box1, col_box2 = st.columns(2)

                # Boxplot 1: per main category
                with col_box1:
                    st.subheader("箱ひげ図 1：業種大分類")
                    # Only show if '業種大分類' column exists and has valid data
                    if '業種大分類' in filtered_df.columns and not filtered_df['業種大分類'].dropna().empty:
                        value_col_main = st.selectbox("数値項目を選択してください (箱ひげ図 1)", numeric_columns, key="boxplot1_value")
                        show_outliers_main = st.checkbox("外れ値を表示 (箱ひげ図 1)", value=True, key="outliers_main")
                        if value_col_main:
                            # Pass necessary arguments to create_boxplot
                            create_boxplot(filtered_df, value_col_main, "業種大分類", show_outliers_main)

                            st.markdown("---") # Add separator line

                            # 要約統計量：業種大分類ごと (Summary Statistics)
                            st.subheader(f"📊 {value_col_main} の要約統計量 (業種大分類別)")
                            try:
                                # Filter out NaN values in grouping column or value column for describe
                                df_describe_main = filtered_df.dropna(subset=['業種大分類', value_col_main]).copy()
                                if not df_describe_main.empty:
                                    # Ensure the value column is numeric before describe
                                    if pd.api.types.is_numeric_dtype(df_describe_main[value_col_main]):
                                        grouped_stats_main = df_describe_main.groupby("業種大分類")[value_col_main].describe()
                                        st.dataframe(grouped_stats_main)
                                    else:
                                        st.warning(f"選択された数値項目 '{value_col_main}' は数値型ではないため、要約統計量を作成できません。")
                                else:
                                     st.warning("要約統計量を作成するための有効なデータがありません。")

                            except Exception as e:
                                st.error(f"業種大分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                    else:
                         st.warning("箱ひげ図と要約統計量を作成するための有効なデータを含む列 '業種大分類' が不足しています。")


                # Boxplot 2: per sub category
                with col_box2:
                    st.subheader("箱ひげ図 2：業種中分類")
                    # Only show if '業種中分類' column exists and has valid data
                    if '業種中分類' in filtered_df.columns and not filtered_df['業種中分類'].dropna().empty:
                        value_col_sub = st.selectbox("数値項目を選択してください (箱ひげ図 2)", numeric_columns, key="boxplot2_value")
                        show_outliers_sub = st.checkbox("外れ値を表示 (箱ひげ図 2)", value=True, key="outliers_sub")
                        if value_col_sub:
                             # Pass necessary arguments to create_boxplot
                             create_boxplot(filtered_df, value_col_sub, "業種中分類", show_outliers_sub)

                             st.markdown("---") # Add separator line

                             # 要約統計量：業種中分類ごと (Summary Statistics)
                             st.subheader(f"📊 {value_col_sub} の要約統計量 (業種中分類別)")
                             try:
                                 # Filter out NaN values in grouping column or value column for describe
                                 df_describe_sub = filtered_df.dropna(subset=['業種中分類', value_col_sub]).copy()
                                 if not df_describe_sub.empty:
                                     # Ensure the value column is numeric before describe
                                     if pd.api.types.is_numeric_dtype(df_describe_sub[value_col_sub]):
                                         grouped_stats_sub = df_describe_sub.groupby("業種中分類")[value_col_sub].describe()
                                         st.dataframe(grouped_stats_sub)
                                     else:
                                        st.warning(f"選択された数値項目 '{value_col_sub}' は数値型ではないため、要約統計量を作成できません。")

                                 else:
                                     st.warning("要約統計量を作成するための有効なデータがありません。")

                             except Exception as e:
                                 st.error(f"業種中分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                    else:
                         st.warning("箱ひげ図と要約統計量を作成するための有効なデータを含む列 '業種中分類' が不足しています。")

            else:
                st.warning("箱ひげ図と要約統計量を作成できる数値項目、または分類項目が見つかりません。")

        else:
             st.warning("フィルター条件に一致するデータがないため、分析結果を表示できません。フィルター設定を調整してください。")


        # --- フィルター後のデータ (Filtered Data - moved to the bottom) ---
        st.header("フィルター後のデータ")
        # Display the filtered_df
        st.dataframe(filtered_df)


    # Message when no file is uploaded or loaded data is empty
    elif uploaded_file is None:
        st.info("分析を開始するには、Excelファイルをアップロードしてください。")
    elif df is None or df.empty:
         st.warning("アップロードされたファイルにデータが含まれていないか、読み込みに失敗しました。ファイル形式を確認してください。")


if __name__ == "__main__":
    main()
