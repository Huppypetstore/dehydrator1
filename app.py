import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Dict

# Define constants for the categories - These will be removed as they are no longer needed.
# MAIN_CATEGORIES = [
#     "エネルギー関連", "クリーニング工場", "レンタル機として保有", "運送業", "下水関連",
#     "化学製品工場", "化学薬品工場", "機械製造業", "工業", "産業廃棄物", "商業施設",
#     "食品製造", "生コン", "製紙", "繊維製品", "畜産", "発電所"
# ]

# SUB_CATEGORIES = [
#     "ガラス", "ごみ処理施設", "ゴム製品", "シャーペンの芯製造工場", "ショッピングモール",
#     "し尿処理場", "その他", "バイオガス", "バイオマス", "ビル", "ホテル",
#     "メタン発酵残渣", "レジャー施設", "レンダリング", "移動脱水車", "飲料",
#     "下水処理場", "化粧品", "外食", "学校", "給食センター", "漁業集落排水",
#     "金属", "健康食品", "自動車・二輪", "樹脂", "浄化槽", "食肉加工",
#     "食品加工", "食料品", "水産加工", "精米", "製パン", "製菓",
#     "製麵", "製薬", "洗剤", "染料", "繊維・衣料", "繊維製品", "調味料",
#     "漬物", "電気・電子部品", "電力", "塗装", "塗装系排水処理", "塗料",
#     "肉牛", "乳飲料", "乳牛（酪農）", "乳製品", "農業集落排水", "農業⇒公共下水",
#     "廃プラ", "プラ再生工場", "発電所", "病院", "薬品", "油田", "溶剤",
#     "養鶏", "養豚", "冷凍・チルド・中食"
# ]

# DEWATERING_MACHINE_TYPES = [
#     "多重円板型脱水機", "多重板型スクリュープレス脱水機"
# ]

def load_and_process_data(uploaded_file) -> pd.DataFrame:
    """Load and process the uploaded Excel file."""
    try:
        df = pd.read_excel(uploaded_file)

        # Ensure necessary columns exist before processing
        required_cols = ['業種大分類', '業種中分類', '受注の有無']
        # '脱水機種別' is used conditionally, check separately
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"必須の列が見つかりません: {', '.join(missing_cols)}")
            return None

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

# ... existing code ...

def main():
    st.set_page_config(page_title="引き合い情報分析 APP", layout="wide")
    st.title("📊 引き合い情報分析 APP")

    # ファイルアップロード
    uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=['xlsx', 'xls'])

    if uploaded_file is not None:
        df = load_and_process_data(uploaded_file)

        if df is not None:
            # データフレームからカテゴリを動的に取得
            # 欠損値を除外し、ユニークな値を取得してソート
            dynamic_order_status = sorted(df['受注の有無'].dropna().unique().tolist())
            dynamic_main_categories = sorted(df['業種大分類'].dropna().unique().tolist())
            dynamic_sub_categories = sorted(df['業種中分類'].dropna().unique().tolist())

            # '脱水機種別'列が存在する場合のみ取得
            dynamic_machine_types = []
            if '脱水機種別' in df.columns:
                 dynamic_machine_types = sorted(df['脱水機種別'].dropna().unique().tolist())

            # フィルター設定
            st.header("フィルター設定")
            # カラム数を確認し、脱水機種別がある場合は4カラム、ない場合は3カラムにする
            num_cols = 4 if dynamic_machine_types else 3
            cols = st.columns(num_cols)

            with cols[0]:
                order_status = st.multiselect(
                    "受注の有無",
                    options=dynamic_order_status, # 動的に取得したリストを使用
                    default=dynamic_order_status # 初期値を全て選択にする
                )
            with cols[1]:
                selected_main_categories = st.multiselect(
                    "業種大分類",
                    options=dynamic_main_categories, # 動的に取得したリストを使用
                    default=[]
                )
            with cols[2]:
                selected_sub_categories = st.multiselect(
                    "業種中分類",
                    options=dynamic_sub_categories, # 動的に取得したリストを使用
                    default=[]
                )
            if dynamic_machine_types: # '脱水機種別'の列が存在する場合のみ表示
                with cols[3]:
                    selected_machine_types = st.multiselect(
                        "脱水機種別",
                        options=dynamic_machine_types, # 動的に取得したリストを使用
                        default=[]
                    )
            else:
                 selected_machine_types = [] # 列が存在しない場合は空リストとする


            filtered_df = df.copy()
            # フィルター処理
            if order_status:
                filtered_df = filtered_df[filtered_df['受注の有無'].isin(order_status)]
            if selected_main_categories:
                filtered_df = filtered_df[filtered_df['業種大分類'].isin(selected_main_categories)]
            if selected_sub_categories:
                filtered_df = filtered_df[filtered_df['業種中分類'].isin(selected_sub_categories)]

            # '脱水機種別'の列が存在し、かつフィルターが選択されている場合のみ適用
            if '脱水機種別' in filtered_df.columns and selected_machine_types:
                 filtered_df = filtered_df[filtered_df['脱水機種別'].isin(selected_machine_types)]


            # 分析結果（件数）
            st.header("分析結果")
            st.write(f"フィルター適用後の総件数: {len(filtered_df)}")

            st.subheader("件数グラフ")
            # '受注の有無'がdynamic_order_statusに含まれていることを確認してから選択肢に追加
            count_chart_options = ["業種大分類", "業種中分類"]
            if '受注の有無' in filtered_df.columns and len(dynamic_order_status) > 0:
                 count_chart_options.append("受注の有無")

            chart_type = st.radio(
                "グラフの種類を選択してください:",
                count_chart_options
            )
            create_summary_chart(filtered_df, chart_type)

            # 数値分析（箱ひげ図と要約統計量）
            st.header("数値分析（箱ひげ図と要約統計量）")
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
                    # 0を表示のチェックボックスは、該当する列を選択した場合にのみ表示する
                    show_zeros_main = False # Initialize
                    columns_to_filter_zero_and_nan = ['固形物回収率 %', '脱水ケーキ含水率 %']
                    if value_col_main in columns_to_filter_zero_and_nan:
                         show_zeros_main = st.checkbox("0を表示", value=False, key="show_zeros_main")

                    if value_col_main and '業種大分類' in filtered_df.columns: # '業種大分類'列が存在するか確認
                        # Filter out NaN values and 0 if show_zeros_main is False
                        df_for_analysis_main = filtered_df.copy()
                        df_for_analysis_main = df_for_analysis_main[df_for_analysis_main[value_col_main].notna()]
                        if value_col_main in columns_to_filter_zero_and_nan and not show_zeros_main:
                             df_for_analysis_main = df_for_analysis_main[df_for_analysis_main[value_col_main] != 0]


                        # Sort categories by count for boxplot
                        if not df_for_analysis_main.empty: # フィルタリング後にデータがあるか確認
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
                                grouped_stats_main = df_for_analysis_main.groupby("業種大分類")[value_col_main].describe()
                                st.dataframe(grouped_stats_main)
                            except Exception as e:
                                st.error(f"業種大分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                        else:
                             st.warning("選択されたフィルターと数値項目で表示するデータがありません。")
                    elif value_col_main:
                         st.warning("箱ひげ図を作成するために必要な「業種大分類」列が見つかりません。")


                with col_box2:
                    # 箱ひげ図 2：業種中分類 ごと
                    st.subheader("箱ひげ図 2：業種中分類")
                    value_col_sub = st.selectbox("数値項目を選択してください", numeric_columns, key="boxplot2_value")
                    show_outliers_sub = st.checkbox("外れ値を表示", value=False, key="outliers_sub")
                     # 0を表示のチェックボックスは、該当する列を選択した場合にのみ表示する
                    show_zeros_sub = False # Initialize
                    columns_to_filter_zero_and_nan = ['固形物回収率 %', '脱水ケーキ含水率 %']
                    if value_col_sub in columns_to_filter_zero_and_nan:
                         show_zeros_sub = st.checkbox("0を表示", value=False, key="show_zeros_sub")

                    if value_col_sub and '業種中分類' in filtered_df.columns: # '業種中分類'列が存在するか確認
                        # Filter out NaN values and 0 if show_zeros_sub is False
                        df_for_analysis_sub = filtered_df.copy()
                        df_for_analysis_sub = df_for_analysis_sub[df_for_analysis_sub[value_col_sub].notna()]
                        if value_col_sub in columns_to_filter_zero_and_nan and not show_zeros_sub:
                             df_for_analysis_sub = df_for_analysis_sub[df_for_analysis_sub[value_col_sub] != 0]


                        # Sort categories by count for boxplot
                        if not df_for_analysis_sub.empty: # フィルタリング後にデータがあるか確認
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
                                grouped_stats_sub = df_for_analysis_sub.groupby("業種中分類")[value_col_sub].describe()
                                st.dataframe(grouped_stats_sub)
                            except Exception as e:
                                st.error(f"業種中分類ごとの要約統計量の計算中にエラーが発生しました: {str(e)}")
                        else:
                             st.warning("選択されたフィルターと数値項目で表示するデータがありません。")
                    elif value_col_sub:
                         st.warning("箱ひげ図を作成するために必要な「業種中分類」列が見つかりません。")

            else:
                st.warning("箱ひげ図と要約統計量を作成できる数値項目が見つかりません。")

            # フィルター後のデータ
            st.header("フィルター後のデータ")
            st.dataframe(filtered_df)

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
