import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Dict
# import os # Removed os import - assuming we are back to Excel only

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

# DEWATERING_MACHINE_TYPES constant was not used in the last version, keeping it commented or removing is fine
# DEWATERING_MACHINE_TYPES = [
#     "多重円板型脱水機", "多重板型スクリュープレス脱水機"
# ]

def load_and_process_data(uploaded_file) -> pd.DataFrame:
    """Load and process the uploaded Excel file."""
    try:
        df = pd.read_excel(uploaded_file)

        # Basic cleaning as in the original code
        # Global Data Cleaning: Replace all 0 (numeric or text) with NaN across the entire dataframe
        df = df.replace(0, pd.NA) # Replace numeric 0
        df = df.replace('0', pd.NA) # Replace text "0"

        # Data Cleaning for specific columns (as in the original code)
        columns_to_clean = ['固形物回収率 %', '脱水ケーキ含水率 %']
        for col in columns_to_clean:
            if col in df.columns:
                # More robust cleaning: convert to string, replace common non-numeric representations, then convert to numeric
                df[col] = df[col].astype(str) # Ensure it's string type
                df[col] = df[col].str.strip() # Remove leading/trailing whitespace
                # Replace common non-numeric indicators of missing or zero with empty string
                df[col] = df[col].replace(['^\s*$', '.', '-', 'N/A'], '', regex=True) # Added '.' and '-' as potential indicators
                df[col] = df[col].replace('', pd.NA) # Replace empty strings with NaN
                # Finally, convert to numeric, coercing errors to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
        return None

def create_boxplot(df: pd.DataFrame, value_col: str) -> None:
    """Create and display a boxplot for the specified value column, grouped by main and sub categories."""
    # Added checks for necessary columns and empty data after filtering/deletion
    if df is not None and not df.empty and "業種大分類" in df.columns and "業種中分類" in df.columns and value_col in df.columns:
         # Drop rows where grouping columns or value column are NaN for plotting
         df_plot = df.dropna(subset=["業種大分類", "業種中分類", value_col]).copy()

         if df_plot.empty:
              st.warning(f"選択されたデータまたは列 ('業種大分類', '業種中分類', '{value_col}') に有効なデータがありません。フィルター設定または削除された行を確認してください。")
              return

         # Sort categories by count for consistent plotting order
         try:
              # Combine main and sub category for sorting the x-axis (optional but can make it cleaner)
              df_plot['Main_Sub'] = df_plot['業種大分類'].astype(str) + ' - ' + df_plot['業種中分類'].astype(str)
              category_counts = df_plot['Main_Sub'].value_counts().reset_index()
              category_counts.columns = ['Main_Sub', 'count']
              sorted_categories = category_counts.sort_values('count', ascending=False)['Main_Sub'].tolist()

              fig = px.box(
                  df_plot,
                  x="Main_Sub", # Use combined category for x-axis if sorting works well
                  y=value_col,
                  color="業種大分類", # Color by main category
                  points="all", # Always show points as per original request
                  title=f"業種大分類×業種中分類ごとの{value_col}の箱ひげ図",
                  category_orders={"Main_Sub": sorted_categories} # Apply sorting
              )
              fig.update_layout(
                  xaxis_tickangle=-45,
                  height=600
              )
              st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

         except Exception as e:
              st.error(f"箱ひげ図の作成中にエラーが発生しました: {str(e)}")
              # Fallback if combined category or sorting causes issues
              st.warning("カテゴリ結合またはソートに問題が発生しました。元のカテゴリでプロットを試みます。")
              try:
                   fig = px.box(
                      df_plot,
                      x="業種大分類", # Fallback to main category on x-axis
                      y=value_col,
                      color="業種中分類",
                      points="all",
                      title=f"業種大分類×業種中分類ごとの{value_col}の箱ひげ図",
                      # No category order applied in fallback
                   )
                   fig.update_layout(
                      xaxis_tickangle=-45,
                      height=600
                   )
                   st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
              except Exception as fallback_e:
                   st.error(f"フォールバックの箱ひげ図作成中にエラーが発生しました: {str(fallback_e)}")


    elif df is not None and df.empty:
         st.warning("箱ひげ図を作成するためのデータがありません。")
    elif df is None:
         st.warning("データがロードされていません。")
    else:
         st.warning("箱ひげ図の作成に必要な列 ('業種大分類', '業種中分類', または選択された数値項目) がデータに存在しません。")


def main():
    st.set_page_config(page_title="顧客情報分析", layout="wide")
    st.title("顧客情報分析システム")

    # Initialize session state for the DataFrame if it doesn't exist
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'filtered_data' not in st.session_state:
        st.session_state.filtered_data = None
    if 'display_data' not in st.session_state:
        st.session_state.display_data = None


    uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=['xlsx', 'xls'])

    # Load data only when a new file is uploaded
    if uploaded_file is not None and st.session_state.data is None:
        st.session_state.data = load_and_process_data(uploaded_file)
        # Initialize filtered_data and display_data with the loaded data
        if st.session_state.data is not None:
             st.session_state.filtered_data = st.session_state.data.copy()
             st.session_state.display_data = st.session_state.data.copy()
             st.success("ファイルが正常にロードされました。")


    # Proceed only if data is loaded
    if st.session_state.data is not None and not st.session_state.data.empty:

        st.subheader("フィルター設定（初期フィルター）")

        col1, col2, col3 = st.columns(3)

        # Get options from the *original* loaded data for initial filters
        # This prevents filter options changing based on previous filters/deletions
        original_df = st.session_state.data
        order_status_options = original_df['受注の有無'].unique().tolist() if '受注の有無' in original_df.columns else []
        main_categories_options = original_df['業種大分類'].unique().tolist() if '業種大分類' in original_df.columns else []
        sub_categories_options = original_df['業種中分類'].unique().tolist() if '業種中分類' in original_df.columns else []


        with col1:
            if '受注の有無' in original_df.columns:
                selectable_order_status_options = [x for x in order_status_options if pd.notna(x)]
                order_status = st.multiselect(
                    "受注の有無",
                    options=[True, False], # Assuming True/False are the only relevant options
                    default=[True, False] if any(x in [True, False] for x in selectable_order_status_options) else []
                )
            else:
                st.warning("列 '受注の有無' がデータに存在しません。初期フィルターは適用されません。")
                order_status = None


        with col2:
            if '業種大分類' in original_df.columns:
                main_categories_options_cleaned = [x for x in main_categories_options if pd.notna(x)]
                selected_main_categories = st.multiselect(
                    "業種大分類",
                    options=main_categories_options_cleaned,
                    default=[]
                )
            else:
                st.warning("列 '業種大分類' がデータに存在しません。初期フィルターは適用されません。")
                selected_main_categories = None


        with col3:
            if '業種中分類' in original_df.columns:
                 sub_categories_options_cleaned = [x for x in sub_categories_options if pd.notna(x)]
                 selected_sub_categories = st.multiselect(
                    "業種中分類",
                    options=sub_categories_options_cleaned,
                    default=[]
                 )
            else:
                 st.warning("列 '業種中分類' がデータに存在しません。初期フィルターは適用されません。")
                 selected_sub_categories = None


        # Apply initial filter from multiselects
        temp_filtered_df = original_df.copy()
        if order_status is not None and order_status and '受注の有無' in temp_filtered_df.columns:
            temp_filtered_df = temp_filtered_df[temp_filtered_df['受注の有無'].isin(order_status)]
        if selected_main_categories is not None and selected_main_categories and '業種大分類' in temp_filtered_df.columns:
            temp_filtered_df = temp_filtered_df[temp_filtered_df['業種大分類'].isin(selected_main_categories)]
        if selected_sub_categories is not None and selected_sub_categories and '業種中分類' in temp_filtered_df.columns:
            temp_filtered_df = temp_filtered_df[temp_filtered_df['業種中分類'].isin(selected_sub_categories)]

        # Update filtered_data and display_data in session state based on initial filters
        # Check if the initial filters resulted in a non-empty DataFrame before updating
        if not temp_filtered_df.empty:
             st.session_state.filtered_data = temp_filtered_df.copy()
             st.session_state.display_data = temp_filtered_df.copy() # display_data starts as filtered_data
        else:
             st.session_state.filtered_data = pd.DataFrame(columns=original_df.columns) # Set to empty df with original columns
             st.session_state.display_data = pd.DataFrame(columns=original_df.columns)
             st.warning("初期フィルター条件に一致するデータがありません。")


        st.subheader("フィルター後のデータ")
        st.write(f"初期フィルター適用後の総件数: {len(st.session_state.filtered_data)}")


        # --- Additional Filtering and Deletion Section ---
        st.subheader("追加のデータ操作")

        # Allow filtering the currently displayed data
        if not st.session_state.display_data.empty:
            cols_for_filter = st.session_state.display_data.columns.tolist()
            filter_col = st.selectbox("フィルターする列を選択", cols_for_filter, key="filter_col")

            # Determine the appropriate input widget based on column dtype
            col_dtype = st.session_state.display_data[filter_col].dtype
            filter_value = None
            if pd.api.types.is_numeric_dtype(col_dtype):
                filter_value = st.number_input(f"'{filter_col}' の値を入力", key="filter_value_numeric")
            elif pd.api.types.is_bool_dtype(col_dtype):
                filter_value = st.checkbox(f"'{filter_col}' の値が True の行を表示", key="filter_value_bool")
            else: # Treat as text for other types (object, category, etc.)
                 filter_value = st.text_input(f"'{filter_col}' の値を入力 (テキスト検索)", key="filter_value_text")


            # Add buttons for applying filter and deleting rows
            col_filter_buttons, col_delete_button = st.columns(2)

            with col_filter_buttons:
                 if st.button("この条件でデータ表示をフィルター"):
                      if filter_value is not None and filter_col in st.session_state.filtered_data.columns:
                           try:
                                # Apply filter to filtered_data to update display_data
                                if pd.api.types.is_numeric_dtype(st.session_state.filtered_data[filter_col].dtype):
                                    # For numeric, strict equality or handle NaN/0 carefully
                                     if pd.isna(filter_value): # If user wants to filter for NaN
                                          st.session_state.display_data = st.session_state.filtered_data[st.session_state.filtered_data[filter_col].isna()].copy()
                                     else:
                                          st.session_state.display_data = st.session_state.filtered_data[st.session_state.filtered_data[filter_col] == filter_value].copy()
                                else: # For other types (text, bool, etc.)
                                     # Ensure the column is string type for filtering
                                     col_data_str = st.session_state.filtered_data[filter_col].astype(str)
                                     st.session_state.display_data = st.session_state.filtered_data[col_data_str.str.contains(str(filter_value), na=False)].copy() # Contains check for text


                                if st.session_state.display_data.empty:
                                     st.warning("指定されたフィルター条件に一致する行が見つかりませんでした。")
                                else:
                                     st.info(f"データ表示を '{filter_col}' == '{filter_value}' でフィルターしました。")

                           except Exception as e:
                                st.error(f"フィルター適用中にエラーが発生しました: {str(e)}")
                      else:
                           st.warning("フィルター条件が有効ではありません。列と値を正しく選択してください。")


            with col_delete_button:
                 if st.button("表示されている行を削除", help="このボタンは、上の『この条件でデータ表示をフィルター』ボタンで現在表示されている行を、初期フィルター後のデータ (分析に使用されるデータ) から完全に削除します。", type="secondary"):
                      if not st.session_state.display_data.empty:
                           # Get the index of the rows currently displayed
                           indices_to_delete = st.session_state.display_data.index
                           # Delete these rows from filtered_data
                           st.session_state.filtered_data = st.session_state.filtered_data.drop(indices_to_delete)
                           # Reset display_data to reflect the deletion (show remaining rows from filtered_data)
                           st.session_state.display_data = st.session_state.filtered_data.copy()
                           st.success(f"{len(indices_to_delete)} 行をデータから削除しました。")
                           # Clear previous filter display message
                           # This might require session state for messages, simpler to just update display data
                      else:
                           st.warning("削除する行がありません。まずフィルターを適用して行を表示してください。")

        elif st.session_state.data is not None and not st.session_state.data.empty:
             # Message when initial filter results in no data
             st.warning("初期フィルター条件に一致するデータがないため、追加の操作はできません。")
        # --- End of Additional Filtering and Deletion Section ---


        # Display the data that will be used for analysis (st.session_state.filtered_data)
        # Use st.data_editor if interactive editing/sorting is desired, otherwise st.dataframe
        st.dataframe(st.session_state.display_data) # Show the data currently in display_data

        st.write(f"分析に使用される総件数 (削除後): {len(st.session_state.filtered_data)}")


        # --- Analysis Results (Boxplot) ---
        st.subheader("分析結果")

        st.subheader("箱ひげ図（業種大分類×業種中分類）")
        # Use st.session_state.filtered_data for analysis
        numeric_columns = st.session_state.filtered_data.select_dtypes(include='number').columns.tolist()

        if numeric_columns:
            # Use a unique key for the selectbox
            value_col = st.selectbox("箱ひげ図に使う数値項目を選択してください", numeric_columns, key="boxplot_value_col")
            # Pass st.session_state.filtered_data to the plotting function
            create_boxplot(st.session_state.filtered_data, value_col)
        else:
            st.warning("分析に使用できる数値項目が見つかりません。")

    # Message when no file is uploaded or loaded data is empty
    elif uploaded_file is None:
        st.info("分析を開始するには、Excelファイルをアップロードしてください。")
    elif st.session_state.data is None or st.session_state.data.empty:
         st.warning("アップロードされたファイルにデータが含まれていないか、読み込みに失敗しました。ファイル形式を確認してください。")


if __name__ == "__main__":
    main()
