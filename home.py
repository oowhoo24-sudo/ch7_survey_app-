import streamlit as st

st.set_page_config(
    page_title="설문 데이터 분석 앱",
    page_icon="📊",
    layout="wide"
)

st.title("📊 설문 데이터 분석 및 정제 시스템")
st.markdown("---")

st.subheader("👋 환영합니다!")
st.write("""
본 애플리케이션은 **구글 설문지 응답 데이터(CSV)**를 업로드하여 정제하고 분석하기 위한 멀티페이지 Streamlit 앱입니다.

왼쪽 사이드바 메뉴를 통해 다음 단계를 진행할 수 있습니다:
1. **데이터 정제 (`1_데이터_정제.py`)**: CSV 업로드, 열 이름 변경, 중복 제거, 이상치/결측치 처리 및 정제 데이터 저장/다운로드
""")

# 세션 상태 초기화 안내
if "clean_df" in st.session_state:
    st.success("✅ 정제된 데이터가 세션에 저장되어 있습니다.")
    st.dataframe(st.session_state["clean_df"].head(), use_container_width=True)
else:
    st.info("💡 사이드바의 **1_데이터_정제** 페이지로 이동하여 CSV 파일을 업로드하고 정제를 진행해 주세요.")
