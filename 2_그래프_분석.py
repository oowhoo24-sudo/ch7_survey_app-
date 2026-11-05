import pandas as pd
import streamlit as st


class SurveyAnalyzer:
    """설문 데이터 분석 및 통계를 처리하는 클래스"""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_summary_metrics(self):
        # 유효 응답 수, 평균 AI 사용 시간, AI 윤리의식 평균 계산
        valid_responses = len(self.df)
        avg_ai_time = (
            self.df["AI사용시간"].mean() if "AI사용시간" in self.df.columns else 0
        )
        avg_ethics = self.df["Q6"].mean() if "Q6" in self.df.columns else 0
        return valid_responses, round(avg_ai_time, 2), round(avg_ethics, 2)

    def get_college_comparison(self, raw_df: pd.DataFrame):
        # 정제 전후 단과대학별 응답자 수 비교 데이터 생성
        clean_counts = (
            self.df["소속단과대학"].value_counts()
            if "소속단과대학" in self.df.columns
            else pd.Series()
        )
        raw_cols = [c for c in raw_df.columns if "단과" in c or "대학" in c]
        if raw_cols:
            raw_counts = raw_df[raw_cols[0]].value_counts()
        else:
            raw_counts = pd.Series()

        comparison_df = pd.DataFrame(
            {"정제 전": raw_counts, "정제 후": clean_counts}
        ).fillna(0)
        return comparison_df

    def get_demographics(self):
        # 성별, 학년, 단과대학 분포 계산
        gender_counts = (
            self.df["성별"].value_counts() if "성별" in self.df.columns else pd.Series()
        )
        grade_counts = (
            self.df["학년"].value_counts().sort_index()
            if "학년" in self.df.columns
            else pd.Series()
        )
        college_counts = (
            self.df["소속단과대학"].value_counts()
            if "소속단과대학" in self.df.columns
            else pd.Series()
        )
        return gender_counts, grade_counts, college_counts

    def get_question_means(self):
        # 문항별 평균 점수 계산
        q_cols = [f"Q{i}" for i in range(1, 7)] + ["Q6R"]
        existing_cols = [c for c in q_cols if c in self.df.columns]
        if existing_cols:
            return self.df[existing_cols].mean().round(2)
        return pd.Series()

    def get_group_comparison(self, group_col: str):
        # 집단별 평균 및 인원수 계산
        numeric_cols = (
            self.df.select_dtypes(include=["number"]).columns.tolist()
        )
        if group_col in self.df.columns and numeric_cols:
            grouped = self.df.groupby(group_col)[numeric_cols].mean().round(2)
            counts = self.df.groupby(group_col).size().rename("인원수")
            result_df = pd.concat([counts, grouped], axis=1)
            return result_df
        return pd.DataFrame()

    def get_scatter_data(self):
        # AI 사용 시간과 Q1 점수 산점도 데이터 추출
        if "AI사용시간" in self.df.columns and "Q1" in self.df.columns:
            return self.df[["AI사용시간", "Q1"]].dropna()
        return pd.DataFrame()


def render_graph_analysis_page():
    # 페이지 설정
    st.set_page_config(page_title="설문 데이터 분석", layout="wide")
    st.title("설문 데이터 분석 및 시각화")
    st.markdown("---")

    target_df = None
    raw_df_for_comparison = None

    # 세션 상태 확인 및 데이터 로드
    if "clean_df" in st.session_state:
        target_df = st.session_state["clean_df"]
        st.info("세션에 저장된 정제된 데이터를 불러왔습니다.")

        uploaded_raw = st.file_uploader(
            "정제 전후 비교를 위한 원본 CSV 파일 업로드 (선택)", type=["csv"]
        )
        if uploaded_raw is not None:
            raw_df_for_comparison = pd.read_csv(uploaded_raw)
        else:
            raw_df_for_comparison = target_df.copy()
    else:
        st.warning(
            "세션에 정제된 데이터가 없습니다. 정제된 CSV 파일을 업로드해주세요."
        )
        uploaded_clean = st.file_uploader(
            "정제된 데이터(CSV) 업로드", type=["csv"], key="clean_upload"
        )
        if uploaded_clean is not None:
            target_df = pd.read_csv(uploaded_clean)
            st.session_state["clean_df"] = target_df
            raw_df_for_comparison = target_df.copy()

    if target_df is not None and not target_df.empty:
        analyzer = SurveyAnalyzer(target_df)

        # 1. 요약 지표
        st.subheader("1. 요약 지표")
        valid_cnt, avg_time, avg_eth = analyzer.get_summary_metrics()
        col1, col2, col3 = st.columns(3)
        col1.metric("유효 응답 수", f"{valid_cnt}명")
        col2.metric("평균 AI 사용 시간", f"{avg_time}분")
        col3.metric("AI 윤리의식 평균(Q6)", f"{avg_eth}점")

        st.markdown("---")

        # 2. 정제 전후 비교
        st.subheader("2. 정제 전후 단과대학별 응답자 수 비교")
        if raw_df_for_comparison is not None:
            comp_df = analyzer.get_college_comparison(raw_df_for_comparison)
            st.bar_chart(comp_df, horizontal=True)
        else:
            st.bar_chart(
                target_df["소속단과대학"].value_counts(), horizontal=True
            )

        st.markdown("---")

        # 3. 탭 구성
        st.subheader("3. 상세 분석 결과")
        tab1, tab2, tab3, tab4 = st.tabs(
            ["응답자 구성", "문항별 평균", "집단 비교", "사용 시간과 점수"]
        )

        with tab1:
            st.markdown("#### 응답자 구성 현황")
            gender_c, grade_c, college_c = analyzer.get_demographics()

            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("성별 분포")
                if not gender_c.empty:
                    st.bar_chart(gender_c, horizontal=True)
            with c2:
                st.write("학년 분포")
                if not grade_c.empty:
                    st.bar_chart(grade_c, horizontal=True)
            with c3:
                st.write("단과대학 분포")
                if not college_c.empty:
                    st.bar_chart(college_c, horizontal=True)

        with tab2:
            st.markdown("#### 문항별 평균 점수")
            q_means = analyzer.get_question_means()
            if not q_means.empty:
                st.bar_chart(q_means, horizontal=True)
                st.dataframe(q_means, use_container_width=True)

        with tab3:
            st.markdown("#### 집단별 비교 (학년 및 단과대학)")
            group_selection = st.selectbox(
                "분석 기준 집단 선택", options=["학년", "소속단과대학"]
            )
            group_result = analyzer.get_group_comparison(group_selection)
            if not group_result.empty:
                st.dataframe(group_result, use_container_width=True)
                plot_data = group_result.drop(columns=["인원수"]).copy()
                plot_data.index.name = None  # 인덱스 이름 충돌 방지
                st.bar_chart(plot_data, horizontal=True)
            else:
                st.write("해당 집단 데이터를 분석할 수 없습니다.")

        with tab4:
            st.markdown("#### AI 사용 시간과 문항 점수 관계")
            scatter_df = analyzer.get_scatter_data()
            if not scatter_df.empty:
                st.scatter_chart(scatter_df, x="AI사용시간", y="Q1")
                st.caption(
                    "AI 사용 시간(X축)과 Q1 점수(Y축)의 분산형 차트입니다."
                )
            else:
                st.write("사용 시간 또는 Q1 데이터가 존재하지 않습니다.")


if __name__ == "__main__":
    render_graph_analysis_page()