import streamlit as st


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: #f4f7f5;
                color: #17251d;
            }

            .stApp h1, .stApp h2, .stApp h3, .stApp p,
            .stApp label, .stApp [data-testid="stCaptionContainer"] {
                color: #17251d;
                letter-spacing: 0 !important;
            }

            .block-container {
                max-width: 1180px;
                padding-top: 1.8rem;
                padding-bottom: 3rem;
            }

            section[data-testid="stSidebar"] {
                background: #0d2d20;
            }

            section[data-testid="stSidebar"] * {
                color: #f4fbf6;
            }

            div[data-baseweb="input"] > div,
            div[data-baseweb="select"] > div,
            div[data-baseweb="textarea"] > div {
                background: #ffffff !important;
                border-color: #b8cabe !important;
                border-radius: 6px !important;
            }

            div[data-baseweb="input"] input,
            div[data-baseweb="textarea"] textarea,
            div[data-baseweb="select"] * {
                color: #17251d !important;
            }

            div[data-baseweb="input"] > div:focus-within,
            div[data-baseweb="select"] > div:focus-within,
            div[data-baseweb="textarea"] > div:focus-within {
                border-color: #0d7563 !important;
                box-shadow: 0 0 0 1px #0d7563 !important;
            }

            div[data-testid="stMetric"] {
                background: #ffffff !important;
                border: 1px solid #d4e0d7 !important;
                border-radius: 6px !important;
                padding: 0.8rem 0.95rem !important;
                box-shadow: 0 1px 2px rgba(14, 39, 27, 0.06) !important;
            }

            div[data-testid="stMetric"] *,
            div[data-testid="stMetric"] p {
                color: #153425 !important;
                opacity: 1 !important;
            }

            label[data-testid="stMetricLabel"] p {
                color: #4a6556 !important;
                font-size: 0.9rem !important;
                font-weight: 800 !important;
            }

            div[data-testid="stMetricValue"] p {
                color: #112b1e !important;
                font-weight: 800 !important;
                letter-spacing: 0 !important;
            }

            div[data-testid="stMetricDelta"] p {
                color: #0d7563 !important;
            }

            .stButton > button,
            .stDownloadButton > button,
            div[data-testid="stLinkButton"] > a {
                min-height: 2.55rem;
                border-radius: 6px;
                font-weight: 700;
                border-color: #a9bfb0;
                color: #173426;
                background: #ffffff;
                box-shadow: none;
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover,
            div[data-testid="stLinkButton"] > a:hover {
                border-color: #0d7563;
                color: #0d4f42;
                background: #f2f8f4;
            }

            button[data-testid="stBaseButton-primary"],
            .stButton > button[kind="primary"],
            div[data-testid="stFormSubmitButton"] > button {
                border-color: #0d7563 !important;
                color: #ffffff !important;
                background: #0d7563 !important;
            }

            button[data-testid="stBaseButton-primary"]:hover,
            .stButton > button[kind="primary"]:hover,
            div[data-testid="stFormSubmitButton"] > button:hover {
                border-color: #084f43 !important;
                color: #ffffff !important;
                background: #084f43 !important;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid #c9d9ce;
                border-radius: 6px;
                overflow: hidden;
            }

            div[data-testid="stAlert"] {
                border-radius: 6px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
