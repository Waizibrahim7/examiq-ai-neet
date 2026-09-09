import streamlit as st


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: #101817;
                color: #edf4ef;
            }

            .stApp h1, .stApp h2, .stApp h3, .stApp p,
            .stApp label, .stApp [data-testid="stCaptionContainer"] {
                color: #edf4ef;
                letter-spacing: 0 !important;
            }

            .block-container {
                max-width: 1180px;
                padding-top: 2rem;
            }

            section[data-testid="stSidebar"] {
                background: #14201d;
            }

            section[data-testid="stSidebar"] * {
                color: #edf4ef;
            }

            div[data-testid="stMetric"] {
                background: #f8fbf9 !important;
                border: 1px solid #cfded4 !important;
                border-radius: 8px !important;
                padding: 0.75rem 0.9rem !important;
                box-shadow: 0 1px 2px rgba(15, 45, 32, 0.08) !important;
            }

            div[data-testid="stMetric"] *,
            div[data-testid="stMetric"] p {
                color: #12372a !important;
                opacity: 1 !important;
            }

            label[data-testid="stMetricLabel"] p {
                color: #43584c !important;
                font-size: 0.98rem !important;
                font-weight: 800 !important;
            }

            div[data-testid="stMetricValue"] p {
                color: #10291f !important;
                font-weight: 800 !important;
                letter-spacing: 0 !important;
            }

            div[data-testid="stMetricDelta"] p {
                color: #1f6b4a !important;
            }

            .stButton > button,
            .stDownloadButton > button {
                border-radius: 8px;
                font-weight: 700;
                border-color: #5d8470;
                color: #edf4ef;
                background: #183f31;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                border-color: #9fcbb1;
                color: #ffffff;
                background: #205440;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid #365143;
                border-radius: 8px;
                overflow: hidden;
            }

            div[data-testid="stAlert"] {
                border-radius: 8px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
