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

def load_and_process_data(uploaded_file) -> pd.DataFrame:
    """Load and process the uploaded Excel file."""
    try:
        df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return None

def create_boxplot(df: pd.DataFrame, value_col: str) -> None:
    """Create and display a boxplot for the specified value column, grouped by main and sub categories."""
    if df is not None and not df.empty:
        fig = px.box(
            df,
            x="業種大分類",
            y=value_col,
            color="業種中分類",
            points="all",
            title=f"業種大分類×業種中分類ごとの{value_col}の箱ひげ図"
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="顧客情報分析", layout="wide")
    st.title("顧客情報分析システム")

    uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=['xlsx', 'xls'])

    if uploaded_file is not None:
        df = load_and_process_data(uploaded_file)
        
        if df is not None:
            st.subheader("フィルター設定")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                order_status = st.multiselect(
                    "受注の有無",
                    options=[True, False],
                    default=[True, False]
                )

            with col2:
                selected_main_categories = st.multiselect(
                    "業種大分類",
                    options=MAIN_CATEGORIES,
                    default=[]
                )

            with col3:
                selected_sub_categories = st.multiselect(
                    "業種中分類",
                    options=SUB_CATEGORIES,
                    default=[]
                )

            filtered_df = df.copy()
            
            if order_status:
                filtered_df = filtered_df[filtered_df['受注の有無'].isin(order_status)]
            
            if selected_main_categories:
                filtered_df = filtered_df[filtered_df['業種大分類'].isin(selected_main_categories)]
            
            if selected_sub_categories:
                filtered_df = filtered_df[filtered_df['業種中分類'].isin(selected_sub_categories)]

            st.subheader("分析結果")
            st.write(f"フィルター適用後の総件数: {len(filtered_df)}")

            st.subheader("箱ひげ図（業種大分類×業種中分類）")
            numeric_columns = filtered_df.select_dtypes(include='number').columns.tolist()
            if numeric_columns:
                value_col = st.selectbox("箱ひげ図に使う数値項目を選択してください", numeric_columns)
                create_boxplot(filtered_df, value_col)
            else:
                st.warning("数値項目が見つかりません。")

            st.subheader("フィルター後のデータ")
            st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
