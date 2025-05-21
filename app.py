import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Dict
import os

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
    """Load and process the uploaded file (Excel or CSV)."""
    df = None # Initialize df to None

    try:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        if file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(uploaded_file)
        elif file_extension == '.csv':
            # Try reading with common Japanese encodings, then UTF-8 as fallback
            encodings_to_try = ['shift_jis', 'cp932', 'utf-8']
            for encoding in encodings_to_try:
                try:
                    uploaded_file.seek(0) # Reset file pointer before trying
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    st.success(f"ファイルを {encoding} エンコーディングで読み込みました。")
                    break # Success, exit loop
                except UnicodeDecodeError:
                    st.warning(f"{encoding} エンコーディングでの読み込みに失敗しました。別のエンコーディングを試します。")
                    continue # Try next encoding
                except Exception as e:
                     st.error(f"{encoding} エンコーディングでの読み込み中に予期しないエラーが発生しました: {str(e)}")
                     # Decide if you want to break or continue on other errors
                     # For now, let's continue trying other encodings
                     continue

            if df is None: # If loop finishes without successful read
                 st.error("CSVファイルの読み込みに失敗しました。Shift-JIS, CP932, UTF-8のいずれのエンコーディングでもデコードできませんでした。ファイルが破損しているか、別のエンコーディングの可能性があります。")
                 return None
        else:
            st.error("サポートされていないファイル形式です。Excel (.xlsx, .xls) または CSV (.csv) ファイルをアップロードしてください。")
            return None

        # --- Data Cleaning and Type Conversion ---

        if df is not None:
            # Global Data Cleaning: Replace all 0 (numeric or text) with NaN across the entire dataframe
            # This is done before specific type conversion to handle '0' strings early
            df = df.replace(0, pd.NA) # Replace numeric 0
            df = df.replace('0', pd.NA) # Replace text "0"

            # List of columns potentially containing numerical data (based on common patterns/units)
            # Add more columns here based on your file's expected structure
            potential_numeric_cols = [
                '固形物回収率 %', '脱水ケーキ含水率 %', # Existing
                'DZx@TS%', 'DZx@SSmg/l', 'VTS%/TS',
                '@ÏWܓY@%/TS', 'ÏW1Y@%/TS', 'ÏW2Y@%/TS',
                'ߑx@kgDS/h', 'EP[Lܐ@', 'Ō`@@',
                'pH@/', 'Mٶؓx@CaCO3mg/', 'Ƶݓx@meq/g-TS',
                'e@ہi#100j@/SS', 'e@ہi#200j@%/SS', 'eς@%/TS',
                'dx@mS/cm', 'n-Hxo mg/l', 'BOD mg/l',
                'CIZx@mg/l', 'Sx@mPa/',
                'XN[]@Hz', 'w@mm', '̉]@ߕ/E',
                'TS@ij', 'VTS/TSij', 'SS@ij', 'VSS/SSij',
                'eVi/TSj', 'Mٶؓx@mgCaCO3/L',
                'dximS/cmj', 'SxX', 'Ǝ풆', 'Ǝ啪',
                'ǊxX', 'D'
                # Add other columns you expect to be numerical here
            ]

            # Attempt to convert these columns to numeric, coercing errors
            for col in potential_numeric_cols:
                if col in df.columns:
                    # Clean specific common non-numeric representations before conversion
                    if df[col].dtype == 'object': # Only apply string cleaning if it's an object/string column
                        df[col] = df[col].astype(str)
                        df[col] = df[col].str.strip()
                        # Replace common non-numeric indicators of missing or zero with empty string before converting to numeric
                        # Adding more potential non-numeric characters often found in data entry
                        df[col] = df[col].replace(['^\s*$', '.', '-', 'N/A', '#VALUE!', '?', '―', '－'], '', regex=True)
                        df[col] = df[col].replace('', pd.NA) # Replace cleaned empty strings with NaN

                    # Convert to numeric, coercing any remaining errors to NaN
                    # Use errors='coerce' to turn unparseable values into NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # After converting to numeric, replace potential remaining 0s with NA if needed
                    # This might be redundant if replace(0, pd.NA) was global, but safer here after conversion
                    df[col] = df[col].replace(0, pd.NA)


            # Data Cleaning for specific columns already in original code (might be redundant after broader conversion, but kept for safety)
            # This part can likely be removed if the broader conversion above is comprehensive
            columns_to_clean_original = ['固形物回収率 %', '脱水ケーキ含水率 %']
            for col in columns_to_clean_original:
                 if col in df.columns and df[col].dtype == 'object': # Only apply if still object type
                      df[col] = df[col].astype(str).str.strip()
                      df[col] = df[col].replace(['^\s*$', '.', '-', 'N/A', '#VALUE!', '?', '―', '－'], '', regex=True)
                      df[col] = df[col].replace('', pd.NA)
                      df[col] = pd.to_numeric(df[col], errors='coerce')
                      df[col] = df[col].replace(0, pd.NA)


        return df
    except Exception as e:
        st.error(f"ファイルの読み込みまたは処理中にエラーが発生しました: {str(e)}")
        return None

# ... rest of the code (create_boxplot, create_summary_chart, main) ...

def create_boxplot(df: pd.DataFrame, value_col: str, category_col: str, show_outliers: bool = True) -> None:
    """Create and display a boxplot for the specified value column, grouped by a specified category.
       Optionally hide outliers."""
    # Ensure the necessary columns exist and are not entirely NaN/empty after filtering
    if df is not None and not df.empty and category_col in df.columns and value_col in df.columns:
        # Filter out rows where the value column or category column is NaN/None
        df_plot = df.dropna(subset=[category_col, value_col]).copy()

        if df_plot.empty:
             st.warning(f"選択された列 ('{category_col}', '{value_col}') に有効なデータがありません（すべての値が欠損値です）。")
             return # Exit if no valid data points for plotting


        points_mode = 'all' if show_outliers else False

        # Sort categories by count for boxplot consistency using the filtered data
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
    elif df is not None and df.empty:
         st.warning(f"選択されたデータまたは列 ({category_col}, {value_col}) に基づいて箱ひげ図を作成できません。フィルター設定を確認してください。")
    elif df is None:
         st.warning("データがロードされていません。")
    else:
         st.warning(f"指定された列 ('{category_col}' または '{value_col}') がデータに存在しません。")


def create_summary_chart(df: pd.DataFrame, group_by: str) -> None:
    """Create and display a bar chart for the specified grouping (count)."""
    # Ensure the necessary column exists and is not entirely NaN/empty after filtering
    if df is not None and not df.empty and group_by in df.columns:
        # Ensure the group_by column is not entirely NA after filtering
        if df[group_by].dropna().empty:
             st.warning(f"選択されたグループ項目 '{group_by}' に有効なデータがありません（すべての値が欠損値です）。")
             return

        # Group by the primary category and then by '脱水機種別' for color splitting
        if group_by in ["業種大分類", "業種中分類"]:
            # Filter for specific 脱水機種別 types and ensure the column exists
            if '脱水機種別' in df.columns:
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
                      st.warning(f"選択された脱水機種別 '{allowed_machine_types}' に一致するデータがありません。")
                      return # Exit if no data matches the machine types
            else:
                 st.warning("グラフ作成に必要な列 '脱水機種別' がデータに存在しません。")
                 return # Exit if '脱水機種別' column is missing

        else:
            # Handle other grouping types
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
         st.warning(f"選択されたデータまたは列 ({group_by}) に基づいて件数グラフを作成できません。フィルター設定を確認してください。")
    elif df is None:
         st.warning("データがロードされていません。")
    else:
         st.warning(f"指定された列 ({group_by}) がデータに存在しません。")


def main():
    st.set_page_config(page_title="引き合い情報分析 APP", layout="wide")
    st.title("📊 引き合い情報分析 APP")

    # ファイルアップロード
    # Added 'csv' to the allowed types
    uploaded_file = st.file_uploader("ExcelまたはCSVファイルをアップロードしてください", type=['xlsx', 'xls', 'csv'])

    df = None # Initialize df outside the if block

    if uploaded_file is not None:
        df = load_and_process_data(uploaded_file)

    if df is not None and not df.empty: # Check if df exists and is not empty
        # フィルター設定
        st.header("フィルター設定")
        col1, col2, col3, col4 = st.columns(4)

        # Get unique options from the loaded DataFrame
        order_status_options = df['受注の有無'].unique().tolist() if '受注の有無' in df.columns else []
        main_categories_options = df['業種大分類'].unique().tolist() if '業種大分類' in df.columns else []
        sub_categories_options = df['業種中分類'].unique().tolist() if '業種中分類' in df.columns else []
        machine_types_options = df['脱水機種別'].unique().tolist() if '脱水機種別' in df.columns else []


        with col1:
            # Check if '受注の有無' column exists before creating multiselect
            if '受注の有無' in df.columns:
                # Handle potential NaN in options if necessary, though multiselect usually handles None
                order_status_options_cleaned = [x for x in order_status_options if pd.notna(x)]
                # Provide True/False options if they exist in the data
                selectable_order_status_options = []
                if True in order_status_options_cleaned:
                     selectable_order_status_options.append(True)
                if False in order_status_options_cleaned:
                     selectable_order_status_options.append(False)


                order_status = st.multiselect(
                    "受注の有無",
                    options=selectable_order_status_options, # Use only True/False if available
                    default=selectable_order_status_options # Default to all available T/F options
                )
            else:
                st.warning("列 '受注の有無' がデータに存在しません。フィルターは適用されません。")
                order_status = None # Set to None if column is missing


        with col2:
            # Check if '業種大分類' column exists before creating multiselect
            if '業種大分類' in df.columns:
                # Remove NaN from options for display
                main_categories_options_cleaned = [x for x in main_categories_options if pd.notna(x)]
                selected_main_categories = st.multiselect(
                    "業種大分類",
                    options=main_categories_options_cleaned, # Use unique non-NaN values from data
                    default=[] # Default to empty
                )
            else:
                st.warning("列 '業種大分類' がデータに存在しません。フィルターは適用されません。")
                selected_main_categories = None # Set to None if column is missing

        with col3:
             # Check if '業種中分類' column exists before creating multiselect
             if '業種中分類' in df.columns:
                 # Remove NaN from options for display
                 sub_categories_options_cleaned = [x for x in sub_categories_options if pd.notna(x)]
                 selected_sub_categories = st.multiselect(
                    "業種中分類",
                    options=sub_categories_options_cleaned, # Use unique non-NaN values from data
                    default=[] # Default to empty
                 )
             else:
                  st.warning("列 '業種中分類' がデータに存在しません。フィルターは適用されません。")
                  selected_sub_categories = None # Set to None if column is missing

        with col4:
            # Check if '脱水機種別' column exists before creating multiselect
            if '脱水機種別' in df.columns:
                # Remove NaN from options for display
                machine_types_options_cleaned = [x for x in machine_types_options if pd.notna(x)]
                selected_machine_types = st.multiselect(
                    "脱水機種別",
                    options=machine_types_options_cleaned, # Use unique non-NaN values from data
                    default=[] # Default to empty
                )
            else:
                 st.warning("列 '脱水機種別' がデータに存在しません。フィルターは適用されません。")
                 selected_machine_types = None # Set to None if column is missing


        filtered_df = df.copy()

        # Apply filters only if the column exists and selections were made (and are not empty lists)
        if order_status is not None and order_status: # Check if order_status is not None and not empty list
            # Include NaN in the filter if it was originally in the options (though we filtered for display)
            # A simpler approach: filter for the selected values
            if '受注の有無' in filtered_df.columns:
                 filtered_df = filtered_df[filtered_df['受注の有無'].isin(order_status)]

        if selected_main_categories is not None and selected_main_categories: # Check if selected_main_categories is not None and not empty list
             if '業種大分類' in filtered_df.columns:
                 filtered_df = filtered_df[filtered_df['業種大分類'].isin(selected_main_categories)]

        if selected_sub_categories is not None and selected_sub_categories: # Check if selected_sub_categories is not None and not empty list
             if '業種中分類' in filtered_df.columns:
                 filtered_df = filtered_df[filtered_df['業種中分類'].isin(selected_sub_categories)]

        # Apply machine type filter only if column exists and selections were made
        if selected_machine_types is not None and selected_machine_types and '脱水機種別' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['脱水機種別'].isin(selected_machine_types)]


        # Analysis results (counts)
        st.header("分析結果")
        st.write(f"フィルター適用後の総件数: {len(filtered_df)}")

        if not filtered_df.empty: # Check if filtered_df is not empty before creating charts
            st.subheader("件数グラフ")
            # Only show chart options if the corresponding columns exist and have non-NaN values
            chart_options = []
            if '業種大分類' in filtered_df.columns and not filtered_df['業種大分類'].dropna().empty:
                chart_options.append("業種大分類")
            if '業種中分類' in filtered_df.columns and not filtered_df['業種中分類'].dropna().empty:
                chart_options.append("業種中分類")
            if '受注の有無' in filtered_df.columns and not filtered_df['受注の有無'].dropna().empty:
                chart_options.append("受注の有無")


            if chart_options:
                 chart_type = st.radio(
                    "グラフの種類を選択してください:",
                    chart_options
                 )
                 create_summary_chart(filtered_df, chart_type)
            else:
                 st.warning("件数グラフを作成できる有効なデータを含む列が見つかりません ('業種大分類', '業種中分類', '受注の有無')")


            # Numerical analysis (boxplot and summary statistics)
            st.header("数値分析（箱ひげ図と要約統計量）")
            # Get numerical columns AFTER potential type conversion in load_and_process_data
            numeric_columns = filtered_df.select_dtypes(include='number').columns.tolist()

            if numeric_columns:
                # Create 2 columns to place boxplots and summary statistics side by side
                col_box1, col_box2 = st.columns(2)

                with col_box1:
                    # Boxplot 1: per main category
                    st.subheader("箱ひげ図 1：業種大分類")
                    # Only show if '業種大分類' column exists and has valid data
                    if '業種大分類' in filtered_df.columns and not filtered_df['業種大分類'].dropna().empty:
                        value_col_main = st.selectbox("数値項目を選択してください (箱ひげ図 1)", numeric_columns, key="boxplot1_value")
                        show_outliers_main = st.checkbox("外れ値を表示 (箱ひげ図 1)", value=True, key="outliers_main")
                        if value_col_main:
                            # create_boxplot function now handles data cleaning and checks internally
                            create_boxplot(filtered_df, value_col_main, "業種大分類", show_outliers_main)

                            st.markdown("---") # Add separator line

                            # Summary statistics: per main category
                            st.subheader(f"📊 {value_col_main} の要約統計量 (業種大分類別)")
                            try:
                                # Filter out NaN values for describe() and ensure columns exist
                                if '業種大分類' in filtered_df.columns and value_col_main in filtered_df.columns:
                                     df_describe_main = filtered_df.dropna(subset=['業種大分類', value_col_main]).copy()
                                     if not df_describe_main.empty:
                                         # Ensure the value column is numeric before describe
                                         if pd.api.types.is_numeric_dtype(df_describe_main[value_col_main]):
                                            grouped_stats_main = df_describe_main.groupby("業種大分類")[value_col_main].describe()
                                            st.dataframe(grouped_stats_main)
                                         else:
                                             st.warning(f"選択された数値項目 '{value_col_main}' は数値型ではありません。")
                                     else:
                                         st.warning("要約統計量を作成するための有効なデータがありません。")
                                else:
                                     st.warning("要約統計量を作成するための列 ('業種大分類' または選択された数値項目) が不足しています。")

                            except Exception as e:
                                st.error(f"業種大分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                    else:
                         st.warning("箱ひげ図と要約統計量を作成するための有効なデータを含む列 '業種大分類' が不足しています。")


                with col_box2:
                    # Boxplot 2: per sub category
                    st.subheader("箱ひげ図 2：業種中分類")
                    # Only show if '業種中分類' column exists and has valid data
                    if '業種中分類' in filtered_df.columns and not filtered_df['業種中分類'].dropna().empty:
                        value_col_sub = st.selectbox("数値項目を選択してください (箱ひげ図 2)", numeric_columns, key="boxplot2_value")
                        show_outliers_sub = st.checkbox("外れ値を表示 (箱ひげ図 2)", value=True, key="outliers_sub")
                        if value_col_sub:
                            # create_boxplot function now handles data cleaning and checks internally
                            create_boxplot(filtered_df, value_col_sub, "業種中分類", show_outliers_sub)

                            st.markdown("---") # Add separator line

                            # Summary statistics: per sub category
                            st.subheader(f"📊 {value_col_sub} の要約統計量 (業種中分類別)")
                            try:
                                # Filter out NaN values for describe() and ensure columns exist
                                if '業種中分類' in filtered_df.columns and value_col_sub in filtered_df.columns:
                                    df_describe_sub = filtered_df.dropna(subset=['業種中分類', value_col_sub]).copy()
                                    if not df_describe_sub.empty:
                                        # Ensure the value column is numeric before describe
                                        if pd.api.types.is_numeric_dtype(df_describe_sub[value_col_sub]):
                                            grouped_stats_sub = df_describe_sub.groupby("業種中分類")[value_col_sub].describe()
                                            st.dataframe(grouped_stats_sub)
                                        else:
                                             st.warning(f"選択された数値項目 '{value_col_sub}' は数値型ではありません。")
                                    else:
                                         st.warning("要約統計量を作成するための有効なデータがありません。")
                                else:
                                     st.warning("要約統計量を作成するための列 ('業種中分類' または選択された数値項目) が不足しています。")
                            except Exception as e:
                                st.error(f"業種中分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                    else:
                         st.warning("箱ひげ図と要約統計量を作成するための有効なデータを含む列 '業種中分類' が不足しています。")

            else:
                st.warning("分析に使用できる数値項目が見つかりません。")

            # Filtered data
            st.header("フィルター後のデータ")
            st.dataframe(filtered_df)
        else:
            st.warning("フィルター条件に一致するデータがありません。フィルター設定を調整してください。")

    # Moved the "Upload a file" message outside the if uploaded_file is not None block
    if uploaded_file is None:
        st.info("分析を開始するには、ExcelまたはCSVファイルをアップロードしてください。")


if __name__ == "__main__":
    main()
