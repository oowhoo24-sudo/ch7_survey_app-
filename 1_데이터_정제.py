import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="데이터 정제", page_icon="🧹", layout="wide")


# --- 시간 변환 함수 ---
def parse_ai_time(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()

    if val_str.isdigit():
        return int(val_str)

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)\s*시간", val_str)
    m_match = re.search(r"(\d+)\s*분", val_str)

    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))

    if not h_match and not m_match:
        digits = re.findall(r"\d+", val_str)
        if digits:
            return int(digits[0])
        return None

    return hours * 60 + minutes


# --- 단과대학 분류 함수 ---
def categorize_college(val):
    if pd.isna(val):
        return "기타"
    val_str = str(val).strip()
    if "인문" in val_str:
        return "인문대학"
    elif "사과" in val_str or "사회" in val_str:
        return "사회과학대학"
    elif "경통" in val_str or "경제" in val_str:
        return "경제통상대학"
    elif "경영" in val_str:
        return "경영대학"
    elif "사범" in val_str:
        return "사범대학"
    else:
        return "기타"


# --- 학년 통일 함수 (안전하게 수정됨) ---
def parse_grade(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()

    digits = re.findall(r"\d+", val_str)
    if digits:
        return int(digits[0])

    korean_num_map = {"일": 1, "이": 2, "삼": 3, "사": 4, "오": 5, "육": 6}
    for k, v in korean_num_map.items():
        if k in val_str:
            return v
    return None


# --- 사이드바 설정 ---
st.sidebar.header("⚙️ 정제 옵션 설정")

ai_time_max = st.sidebar.slider(
    "AI 사용 시간 이상치 상한 (분)",
    min_value=30,
    max_value=1440,
    value=300,
    step=30,
)

na_option = st.sidebar.radio(
    "결측치(빈칸) 처리 방식", options=["그대로 두기", "행 삭제"], index=0
)


# --- 메인 화면 ---
st.title("🧹 데이터 정제 (Data Cleaning)")

uploaded_file = st.file_uploader(
    "구글 설문지 CSV 파일(survey_raw.csv)을 업로드하세요.", type=["csv"]
)

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)

    st.subheader("📋 원본 데이터 정보")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric(label="총 응답자 수", value=f"{len(raw_df)} 명")
    with col2:
        st.caption("원본 데이터 미리보기")
        st.dataframe(raw_df.head(3), use_container_width=True)

    st.markdown("---")

    clean_df = raw_df.copy()
    initial_rows = len(clean_df)
    clean_log = []

    # 1. 열 제목 변경
    new_cols = [
        "타임스탬프",
        "성별",
        "학년",
        "소속단과대학",
        "AI사용시간",
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5",
        "Q6",
        "서술형",
    ]
    if len(clean_df.columns) == len(new_cols):
        clean_df.columns = new_cols
        clean_log.append({"정제 항목": "1. 열 제목 변경", "상세 내용": "단축 표준명으로 변경 완료"})
    else:
        clean_df.columns = new_cols[: len(clean_df.columns)]
        clean_log.append(
            {
                "정제 항목": "1. 열 제목 변경",
                "상세 내용": f"열 이름 변경 완료 ({len(clean_df.columns)}개 열)",
            }
        )

    # 2. 중복 제거
    subset_cols = [c for c in clean_df.columns if c != "타임스탬프"]
    before_dup = len(clean_df)
    clean_df = clean_df.drop_duplicates(subset=subset_cols, keep="first")
    dup_removed = before_dup - len(clean_df)
    clean_log.append(
        {
            "정제 항목": "2. 중복 제거",
            "상세 내용": f"타임스탬프 제외 중복 행 {dup_removed}건 제거",
        }
    )

    # 3. 학년 표기 통일
    if "학년" in clean_df.columns:
        clean_df["학년"] = clean_df["학년"].apply(parse_grade)
        clean_log.append(
            {"정제 항목": "3. 학년 통일", "상세 내용": "숫자 형식(1, 2, ...)으로 통일"}
        )

    # 4. 단과대학 분류
    if "소속단과대학" in clean_df.columns:
        clean_df["소속단과대학"] = clean_df["소속단과대학"].apply(categorize_college)
        clean_log.append(
            {"정제 항목": "4. 단과대학 분류", "상세 내용": "6개 범주 재분류"}
        )

    # 5. AI 사용 시간 이상치 처리
    if "AI사용시간" in clean_df.columns:
        clean_df["AI사용시간"] = clean_df["AI사용시간"].apply(parse_ai_time)
        before_outlier = len(clean_df)
        clean_df = clean_df[
            (clean_df["AI사용시간"].notna())
            & (clean_df["AI사용시간"] <= ai_time_max)
        ]
        outlier_removed = before_outlier - len(clean_df)
        clean_log.append(
            {
                "정제 항목": "5. 이상치 제거",
                "상세 내용": f"분 단위 변환 및 {ai_time_max}분 초과 이상치 {outlier_removed}건 제거",
            }
        )

    # 6. 결측치 처리
    null_counts = clean_df.isnull().sum().to_dict()
    null_str = ", ".join([f"{k}: {v}개" for k, v in null_counts.items() if v > 0])
    if not null_str:
        null_str = "결측치 없음"

    if na_option == "행 삭제":
        before_na = len(clean_df)
        clean_df = clean_df.dropna()
        na_removed = before_na - len(clean_df)
        clean_log.append(
            {
                "정제 항목": "6. 결측치 처리",
                "상세 내용": f"행 삭제 적용 -> 총 {na_removed}행 삭제됨",
            }
        )
    else:
        clean_log.append(
            {
                "정제 항목": "6. 결측치 처리",
                "상세 내용": f"그대로 두기 적용 (결측치: {null_str})",
            }
        )

    # 7. 점수 역채점 (Q6R = 6 - Q6)
    if "Q6" in clean_df.columns:
        clean_df["Q6"] = pd.to_numeric(clean_df["Q6"], errors="coerce")
        clean_df["Q6R"] = 6 - clean_df["Q6"]
        clean_log.append(
            {
                "정제 항목": "7. 역채점 재계산",
                "상세 내용": "Q6R 열 신설 (Q6R = 6 - Q6)",
            }
        )

    # --- 결과 요약 카드 표시 ---
    st.subheader("📊 데이터 정제 요약 결과")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("원본 데이터 수", f"{initial_rows} 건")
    m2.metric("최종 정제 데이터 수", f"{len(clean_df)} 건")
    m3.metric("제거된 데이터 수", f"{initial_rows - len(clean_df)} 건")
    m4.metric(
        "데이터 유지율",
        f"{round((len(clean_df) / initial_rows) * 100, 1) if initial_rows > 0 else 0}%",
    )

    # --- 정제 기록 표 ---
    st.markdown("#### 📜 정제 작업 기록")
    st.table(pd.DataFrame(clean_log))

    # --- 최종 정제 데이터 표시 ---
    st.subheader("✨ 정제된 최종 데이터")
    st.dataframe(clean_df, use_container_width=True)

    # --- session_state 저장 및 CSV 다운로드 ---
    st.session_state["clean_df"] = clean_df

    csv_data = clean_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 정제된 데이터 CSV 다운로드",
        data=csv_data,
        file_name="survey_cleaned.csv",
        mime="text/csv",
        type="primary",
    )

else:
    st.warning("👈 왼쪽 상단에서 `survey_raw.csv` 파일을 업로드해 주세요.")