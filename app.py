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

DEWATERING_MACHINE_TYPES = [
    "多重円板型脱水機", "多重板型スクリュープレス脱水機"
]

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
              st.warning(f"箱ひげ図を作成するための有効なデータがありません。選択された列 ('業種大分類', '業種中分類', '{value_col}') の値がすべて欠損値であるか、フィルター/削除によってデータがなくなりました。")
              return

         # Sort categories by count for consistent plotting order
         try:
              # Combine main and sub category for sorting the x-axis
              # Ensure columns are string type for combination to avoid type errors with NaN/None
              df_plot['Main_Sub'] = df_plot['業種大分類'].astype(str) + ' - ' + df_plot['業種中分類'].astype(str)
              category_counts = df_plot['Main_Sub'].value_counts().reset_index()
              category_counts.columns = ['Main_Sub', 'count']
              sorted_categories = category_counts.sort_values('count', ascending=False)['Main_Sub'].tolist()

              fig = px.box(
                  df_plot,
                  x="Main_Sub", # Use combined category for x-axis
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
                   # Fallback: Plot without explicit category order
                   fig = px.box(
                      df_plot,
                      x="業種大分類", # Fallback to main category on x-axis
                      y=value_col,
                      color="業種中分類",
                      points="all",
                      title=f"業種大分類×業種中分類ごとの{value_col}の箱ひげ図",
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


def create_summary_chart(df: pd.DataFrame, group_by: str) -> None:
    """Create and display a bar chart for the specified grouping (count)."""
    # Ensure the necessary column exists and is not entirely NaN/empty after filtering
    if df is not None and not df.empty and group_by in df.columns:
        # Ensure the group_by column is not entirely NA after filtering
        if df[group_by].dropna().empty:
             st.warning(f"件数グラフを作成するための有効なデータがありません。選択されたグループ項目 '{group_by}' の値がすべて欠損値であるか、フィルター/削除によってデータがなくなりました。")
             return

        # Group by the primary category and then by '脱水機種別' for color splitting
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
         st.warning(f"件数グラフを作成するためのデータがありません。フィルター設定または削除された行を確認してください。")
    elif df is None:
         st.warning("データがロードされていません。")
    else:
         st.warning(f"件数グラフの作成に必要な列 ('{group_by}') がデータに存在しません。")


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
    # Add a key to session state to force rerun after deletion
    if 'delete_trigger' not in st.session_state:
        st.session_state.delete_trigger = 0


    uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=['xlsx', 'xls'])

    # Load data only when a new file is uploaded OR if session state was cleared
    # Use a button to trigger load if needed, or rely on uploader hash change
    if uploaded_file is not None:
        # Check if a new file is uploaded by comparing hashes or names if possible
        # Streamlit's file_uploader handles this internally by resetting the widget state
        # when a new file is chosen.
        # Reset session state if a new file is uploaded.
        if st.session_state.data is None or uploaded_file.file_id != getattr(st.session_state.uploaded_file_info, 'file_id', None):
             st.session_state.data = load_and_process_data(uploaded_file)
             # Store file info to detect if a new file is uploaded next time
             st.session_state.uploaded_file_info = uploaded_file
             # Initialize filtered_data and display_data with the loaded data
             if st.session_state.data is not None:
                  st.session_state.filtered_data = st.session_state.data.copy()
                  st.session_state.display_data = st.session_state.data.copy()
                  st.success("ファイルが正常にロードされました。")
             else:
                 # Handle case where loading fails
                 st.session_state.data = None
                 st.session_state.filtered_data = None
                 st.session_state.display_data = None


    # Proceed only if data is loaded in session state
    if st.session_state.data is not None and not st.session_state.data.empty:

        st.subheader("初期フィルター設定")

        col1, col2, col3 = st.columns(3)

        # Get options from the *original* loaded data for initial filters
        original_df = st.session_state.data
        order_status_options = original_df['受注の有無'].unique().tolist() if '受注の有無' in original_df.columns else []
        main_categories_options = original_df['業種大分類'].unique().tolist() if '業種大分類' in original_df.columns else []
        sub_categories_options = original_df['業種中分類'].unique().tolist() if '業種中分類' in original_df.columns else []


        with col1:
            if '受注の有無' in original_df.columns:
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
                    st.warning("列 '受注の有無' に True/False 値が見つかりません。初期フィルターは適用されません。")
                    order_status = None # No options means no filter applied


            else:
                st.warning("列 '受注の有無' がデータに存在しません。初期フィルターは適用されません。")
                order_status = None


        with col2:
            if '業種大分類' in original_df.columns:
                # Remove NaN from options for display
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
                 # Remove NaN from options for display
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
        # Create a temporary DataFrame for filtering based on the *original* data
        temp_filtered_df = original_df.copy()

        if order_status is not None and order_status and '受注の有無' in temp_filtered_df.columns:
             # Filter for the selected boolean values
             temp_filtered_df = temp_filtered_df[temp_filtered_df['受注の有無'].isin(order_status)]

        if selected_main_categories is not None and selected_main_categories and '業種大分類' in temp_filtered_df.columns:
            temp_filtered_df = temp_filtered_df[temp_filtered_df['業種大分類'].isin(selected_main_categories)]

        if selected_sub_categories is not None and selected_sub_categories and '業種中分類' in temp_filtered_df.columns:
            temp_filtered_df = temp_filtered_df[temp_filtered_df['業種中分類'].isin(selected_sub_categories)]


        # Update filtered_data and display_data in session state based on initial filters
        # Check if the initial filters resulted in a non-empty DataFrame before updating
        # This update should happen *before* the additional filtering section is processed in this run
        if not temp_filtered_df.empty:
             # Only update if the filter settings have changed or if it's the first load
             # A simple way to detect changes is to compare lengths, though not perfect
             if len(temp_filtered_df) != len(st.session_state.filtered_data):
                  st.session_state.filtered_data = temp_filtered_df.copy()
                  st.session_state.display_data = temp_filtered_df.copy() # display_data starts as filtered_data
             # If filter settings haven't changed but display_data was manipulated,
             # we need to make sure display_data is consistent with filtered_data unless
             # an additional filter was just applied. This is tricky with Streamlit's rerun.
             # Let's rely on the buttons below to manage display_data.

             # Ensure display_data is at least the initially filtered data if no additional filter applied yet in this run
             # This is complex due to Streamlit's flow. Let's trust the button actions to set display_data.

             pass # Initial filtering is applied to temp_filtered_df, session state is updated below


        else:
             # If initial filter results in empty data, clear session state dataframes used for analysis/display
             st.session_state.filtered_data = pd.DataFrame(columns=original_df.columns) # Set to empty df with original columns
             st.session_state.display_data = pd.DataFrame(columns=original_df.columns)
             st.warning("初期フィルター条件に一致するデータがありません。")


        st.subheader("追加のデータ操作（表示データのフィルターと削除）")

        # --- Additional Filtering and Deletion Section ---
        # Apply additional filters and deletion to st.session_state.filtered_data
        # The display_data reflects the result of additional filtering

        if st.session_state.filtered_data is not None and not st.session_state.filtered_data.empty:

            cols_for_filter = st.session_state.filtered_data.columns.tolist()

            # Use columns for additional filtering section
            col_filter_selector, col_filter_value, col_filter_buttons = st.columns([0.3, 0.4, 0.3])

            with col_filter_selector:
                filter_col = st.selectbox("フィルターする列を選択", cols_for_filter, key="filter_col")

            with col_filter_value:
                # Determine the appropriate input widget based on column dtype
                # Use the dtype from filtered_data as it's the source for additional filter
                if filter_col and filter_col in st.session_state.filtered_data.columns:
                    col_dtype = st.session_state.filtered_data[filter_col].dtype
                    filter_value = None
                    if pd.api.types.is_numeric_dtype(col_dtype):
                        # Allow filtering for NaN in numeric columns
                        filter_for_nan = st.checkbox("欠損値をフィルター", key="filter_nan_checkbox")
                        if not filter_for_nan:
                            filter_value = st.number_input(f"'{filter_col}' の値を入力", key="filter_value_numeric")
                        else:
                            filter_value = pd.NA # Representing NaN filter
                    elif pd.api.types.is_bool_dtype(col_dtype):
                         filter_value_bool = st.radio(f"'{filter_col}' の値をフィルター", options=[True, False, 'すべて'], index=2, key="filter_value_bool")
                         if filter_value_bool == 'すべて':
                             filter_value = None # No filter
                         else:
                             filter_value = filter_value_bool
                    else: # Treat as text for other types (object, category, etc.)
                        filter_value = st.text_input(f"'{filter_col}' の値を入力 (部分一致検索)", key="filter_value_text")
                else:
                     st.warning("フィルターする列を選択してください。")
                     filter_value = None # No valid column selected


            with col_filter_buttons:
                 st.markdown("<br>", unsafe_allow_html=True) # Add some vertical space to align buttons
                 if st.button("表示データをフィルター"):
                      if filter_col and filter_value is not None: # filter_value can be pd.NA for NaN filter
                           try:
                                # Apply filter to filtered_data to update display_data
                                df_to_filter = st.session_state.filtered_data.copy() # Work on a copy

                                if pd.api.types.is_numeric_dtype(df_to_filter[filter_col].dtype):
                                    if pd.isna(filter_value): # Filtering for NaN
                                         st.session_state.display_data = df_to_filter[df_to_filter[filter_col].isna()].copy()
                                    else: # Filtering for a specific numeric value
                                         # Ensure comparison is robust to NaNs in the column
                                         st.session_state.display_data = df_to_filter[df_to_filter[filter_col] == filter_value].copy()

                                elif pd.api.types.is_bool_dtype(df_to_filter[filter_col].dtype) and filter_value is not None:
                                     # Handle boolean filtering, ensure column has boolean dtype
                                     st.session_state.display_data = df_to_filter[df_to_filter[filter_col] == filter_value].copy()

                                else: # Text filtering (or other types treated as text)
                                     # Ensure the column is string type for filtering, handle potential NaNs in column
                                     col_data_str = df_to_filter[filter_col].astype(str).str.lower().fillna('') # Convert to string, lowercase, fill NaN
                                     search_string = str(filter_value).lower() # Convert search value to string and lowercase
                                     st.session_state.display_data = df_to_filter[col_data_str.str.contains(search_string, na=False)].copy() # Case-insensitive contains check

                                if st.session_state.display_data.empty:
                                     st.warning("指定されたフィルター条件に一致する行が見つかりませんでした。")
                                else:
                                     st.info(f"データ表示をフィルターしました ('{filter_col}' に '{filter_value}' が含まれる行)。")

                           except Exception as e:
                                st.error(f"データ表示のフィルター中にエラーが発生しました: {str(e)}")
                      else:
                           st.warning("有効なフィルター列と値を指定してください。")

                 # Button to reset display filter
                 if st.button("表示フィルターをクリア"):
                      # Reset display_data back to the state of filtered_data
                      st.session_state.display_data = st.session_state.filtered_data.copy()
                      st.info("表示フィルターをクリアしました。")


        # Display the data that is currently selected for display
        st.dataframe(st.session_state.display_data)


        # Delete button - This deletes from filtered_data based on what's currently displayed
        if st.session_state.display_data is not None and not st.session_state.display_data.empty:
            if st.button("⬆️ 上記表示されている行をデータから完全に削除", help="このボタンは、上のテーブルに現在表示されている行を、分析に使用されるデータから完全に削除します。"):
                try:
                    # Get the index of the rows currently displayed in display_data
                    indices_to_delete = st.session_state.display_data.index
                    # Check if these indices exist in filtered_data before dropping
                    if not indices_to_delete.empty and all(idx in st.session_state.filtered_data.index for idx in indices_to_delete):
                        # Delete these rows from filtered_data
                        st.session_state.filtered_data = st.session_state.filtered_data.drop(indices_to_delete)
                        # After deleting from filtered_data, reset display_data to show the remaining rows in filtered_data
                        st.session_state.display_data = st.session_state.filtered_data.copy()
                        st.success(f"{len(indices_to_delete)} 行をデータから削除しました。分析に使用されるデータの総件数: {len(st.session_state.filtered_data)}")
                        # Increment trigger to force a rerun and update charts/stats
                        st.session_state.delete_trigger += 1
                        st.experimental_rerun() # Rerun to update the page based on deleted data
                    elif not indices_to_delete.empty:
                         st.warning("表示されている行の一部またはすべてが、既に削除されているかデータソースに存在しません。表示を更新します。")
                         st.session_state.display_data = st.session_state.filtered_data.copy() # Attempt to resync display
                    else:
                         st.warning("削除する行が選択されていません（テーブルに表示されている行がありません）。")

                except Exception as e:
                    st.error(f"行の削除中にエラーが発生しました: {str(e)}")
        elif st.session_state.filtered_data is not None and not st.session_state.filtered_data.empty:
            st.info("追加のフィルターを適用して削除したい行を表示してください。") # Message when filtered_data has rows but display_data is empty
        # --- End of Additional Filtering and Deletion Section ---


        st.write(f"分析に使用されるデータの総件数 (削除後): {len(st.session_state.filtered_data)}")


        # --- Analysis Results ---
        st.header("分析結果")

        # Add back the summary charts section
        st.subheader("件数グラフ")
        # Only show chart options if the corresponding columns exist and have non-NaN values
        chart_options = []
        if '業種大分類' in st.session_state.filtered_data.columns and not st.session_state.filtered_data['業種大分類'].dropna().empty:
            chart_options.append("業種大分類")
        if '業種中分類' in st.session_state.filtered_data.columns and not st.session_state.filtered_data['業種中分類'].dropna().empty:
            chart_options.append("業種中分類")
        if '受注の有無' in st.session_state.filtered_data.columns and not st.session_state.filtered_data['受注の有無'].dropna().empty:
            chart_options.append("受注の有無")

        if chart_options:
             # Use a unique key for the radio button
             chart_type = st.radio(
                "グラフの種類を選択してください:",
                chart_options,
                key="summary_chart_type"
             )
             # Pass st.session_state.filtered_data to the plotting function
             create_summary_chart(st.session_state.filtered_data, chart_type)
        else:
             st.warning("件数グラフを作成できる有効なデータを含む列が見つかりません ('業種大分類', '業種中分類', '受注の有無')")


        # Add back the boxplot section
        st.subheader("数値分析（箱ひげ図）")
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
    elif uploaded_file is None and st.session_state.data is None:
        st.info("分析を開始するには、Excelファイルをアップロードしてください。")
    elif st.session_state.data is None or st.session_state.data.empty:
         st.warning("アップロードされたファイルにデータが含まれていないか、読み込みに失敗しました。ファイル形式を確認してください。")


if __name__ == "__main__":
    main()
