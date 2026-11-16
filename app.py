# ============================================================
# ANALYTIX AI - COMPLETE DATA ANALYTICS APPLICATION
# Optimized Edition
# ============================================================

import os
import json
import uuid
import shutil
import traceback
import re
import hashlib
import textwrap
from pathlib import Path
from datetime import datetime
from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Analytix AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_DIR = Path(__file__).resolve().parent

DATA_DIR = APP_DIR / ".analytix_data"
DATASETS_DIR = DATA_DIR / "datasets"
OUTPUTS_DIR = DATA_DIR / "outputs"
REPORTS_DIR = DATA_DIR / "reports"
CHARTS_DIR = DATA_DIR / "charts"

WORKSPACE_FILE = DATA_DIR / "workspace.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

MAX_ACTIVITY = 100
MAX_OUTPUTS = 200
MAX_CHATS = 200
MAX_DATASETS = 50

for folder in [
    DATA_DIR,
    DATASETS_DIR,
    OUTPUTS_DIR,
    REPORTS_DIR,
    CHARTS_DIR
]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "dataset": None,
    "dataset_name": None,
    "dataset_path": None,
    "dataset_id": None,

    "cleaned_dataset": None,
    "cleaned_dataset_path": None,

    # Persistent section outputs
    "generated_chart_config": None,
    "last_outlier_analysis": None,

    "chat_history": [],

    "ai_insights": None,
    "agent_result": None,
    "agent_explanation": None,
    "analysis_result": None,

    # Automated AI Analyst
    "automated_analysis": None,
    "automated_analysis_charts": [],
    "automated_analysis_dataset_id": None,
    "automated_analysis_path": None,
    "autonomous_analysis": None,

    "current_page": "🏠 Dashboard",

    "workspace": [],
    "activity": [],
    "dataset_registry": [],

    "_workspace_initialized": False,
    "_last_upload_signature": None
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def current_time():

    return datetime.now().strftime(
        "%d %b %Y - %I:%M %p"
    )


def safe_filename(name):

    name = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        str(name)
    )

    return name.strip() or "Analytix_AI"


def safe_file_path(path):

    try:

        resolved = Path(path).resolve()

        allowed_dirs = [
            DATASETS_DIR.resolve(),
            OUTPUTS_DIR.resolve(),
            REPORTS_DIR.resolve(),
            CHARTS_DIR.resolve()
        ]

        return any(
            resolved == folder or folder in resolved.parents
            for folder in allowed_dirs
        )

    except Exception:

        return False


def safe_delete_file(path):

    try:

        path = Path(path)

        if path.exists() and safe_file_path(path):

            path.unlink()

            return True

    except Exception:

        pass

    return False


def save_json_atomic(path, data):

    path = Path(path)

    temp_path = path.with_suffix(".tmp")

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    temp_path.replace(path)


# ============================================================
# PERSISTENT WORKSPACE ENGINE
# ============================================================

def load_workspace():

    if WORKSPACE_FILE.exists():

        try:

            with open(
                WORKSPACE_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if isinstance(data, dict):

                return data

        except Exception:

            pass

    return {
        "workspace": [],
        "activity": [],
        "chat_history": [],
        "dataset_registry": [],
        "current_dataset": None
    }


def save_workspace():

    data = {
        "workspace": st.session_state.workspace,
        "activity": st.session_state.activity,
        "chat_history": st.session_state.chat_history,
        "dataset_registry": st.session_state.dataset_registry,
        "current_dataset": st.session_state.dataset_id
    }

    try:

        save_json_atomic(
            WORKSPACE_FILE,
            data
        )

    except Exception as error:

        st.error(
            f"Workspace save error: {error}"
        )


def initialize_workspace():

    data = load_workspace()

    st.session_state.workspace = data.get(
        "workspace",
        []
    )

    st.session_state.activity = data.get(
        "activity",
        []
    )

    st.session_state.chat_history = data.get(
        "chat_history",
        []
    )

    st.session_state.dataset_registry = data.get(
        "dataset_registry",
        []
    )

    saved_dataset = data.get(
        "current_dataset"
    )

    if saved_dataset:

        for item in st.session_state.dataset_registry:

            if item.get("id") == saved_dataset:

                path = Path(item.get("path", ""))

                if path.exists():

                    try:

                        st.session_state.dataset = pd.read_csv(path)

                        st.session_state.dataset_name = item["name"]

                        st.session_state.dataset_path = str(path)

                        st.session_state.dataset_id = item["id"]

                    except Exception:

                        pass

                break


if not st.session_state._workspace_initialized:

    initialize_workspace()

    st.session_state._workspace_initialized = True


# ============================================================
# ACTIVITY LOG
# ============================================================

def log_activity(
    message,
    category="General",
    persist=True
):

    activity = {
        "id": str(uuid.uuid4()),
        "message": str(message),
        "category": category,
        "time": current_time()
    }

    st.session_state.activity.insert(
        0,
        activity
    )

    st.session_state.activity = (
        st.session_state.activity[:MAX_ACTIVITY]
    )

    if persist:

        save_workspace()


def clear_activity():

    st.session_state.activity = []

    save_workspace()


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(
    title,
    content,
    category="Result"
):

    output_id = str(uuid.uuid4())

    output_path = OUTPUTS_DIR / (
        f"{output_id}.txt"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(str(content))

    output = {
        "id": output_id,
        "title": title,
        "category": category,
        "path": str(output_path),
        "created": current_time()
    }

    st.session_state.workspace.insert(
        0,
        output
    )

    st.session_state.workspace = (
        st.session_state.workspace[:MAX_OUTPUTS]
    )

    save_workspace()

    log_activity(
        f"Saved: {title}",
        category
    )

    return output_id


def delete_output(output_id):

    updated_workspace = []

    for item in st.session_state.workspace:

        if item.get("id") == output_id:

            safe_delete_file(
                item.get("path", "")
            )

        else:

            updated_workspace.append(item)

    st.session_state.workspace = (
        updated_workspace
    )

    save_workspace()

    log_activity(
        "Saved output deleted",
        "Workspace"
    )


def clear_workspace():

    for item in st.session_state.workspace:

        safe_delete_file(
            item.get("path", "")
        )

    st.session_state.workspace = []

    save_workspace()

    log_activity(
        "All saved outputs cleared",
        "Workspace"
    )


# ============================================================
# CHAT PERSISTENCE
# ============================================================

def save_chat(question, answer):

    chat = {
        "id": str(uuid.uuid4()),
        "question": str(question),
        "answer": str(answer),
        "created": current_time()
    }

    st.session_state.chat_history.insert(
        0,
        chat
    )

    st.session_state.chat_history = (
        st.session_state.chat_history[:MAX_CHATS]
    )

    save_workspace()


def delete_chat(chat_id):

    st.session_state.chat_history = [
        item
        for item in st.session_state.chat_history
        if item.get("id") != chat_id
    ]

    save_workspace()

    log_activity(
        "Conversation deleted",
        "Chat"
    )


def clear_chat_history():

    st.session_state.chat_history = []

    save_workspace()

    log_activity(
        "All conversations cleared",
        "Chat"
    )


# ============================================================
# DATASET MANAGEMENT
# ============================================================

def read_dataset(uploaded_file):

    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    if extension == ".csv":

        try:

            return pd.read_csv(
                uploaded_file,
                encoding="utf-8"
            )

        except UnicodeDecodeError:

            uploaded_file.seek(0)

            return pd.read_csv(
                uploaded_file,
                encoding="latin-1"
            )

    elif extension == ".xlsx":

        return pd.read_excel(
            uploaded_file
        )

    raise ValueError(
        "Unsupported dataset format"
    )


def save_dataset(
    df,
    original_name
):

    dataset_id = str(uuid.uuid4())

    filename = f"{dataset_id}.csv"

    path = DATASETS_DIR / filename

    df.to_csv(
        path,
        index=False
    )

    registry_item = {
        "id": dataset_id,
        "name": original_name,
        "path": str(path),
        "rows": len(df),
        "columns": len(df.columns),
        "created": current_time()
    }

    st.session_state.dataset_registry.insert(
        0,
        registry_item
    )

    # Dataset history limit

    removed_items = (
        st.session_state.dataset_registry[MAX_DATASETS:]
    )

    st.session_state.dataset_registry = (
        st.session_state.dataset_registry[:MAX_DATASETS]
    )

    for item in removed_items:

        if item.get("id") != dataset_id:

            safe_delete_file(
                item.get("path", "")
            )

    # Active dataset

    st.session_state.dataset = df.copy()

    st.session_state.dataset_name = original_name

    st.session_state.dataset_path = str(path)

    st.session_state.dataset_id = dataset_id

    # Reset automated analysis

    reset_automated_analysis()

    # Reset dataset dependent results

    st.session_state.cleaned_dataset = None

    st.session_state.cleaned_dataset_path = None

    st.session_state.generated_chart_config = None
    st.session_state.last_outlier_analysis = None

    st.session_state.ai_insights = None

    st.session_state.agent_result = None

    st.session_state.agent_explanation = None

    save_workspace()

    log_activity(
        f"Dataset loaded: {original_name}",
        "Dataset"
    )


def restore_dataset(dataset_id):

    for item in st.session_state.dataset_registry:

        if item.get("id") == dataset_id:

            path = Path(
                item.get("path", "")
            )

            if not path.exists():

                return False

            try:

                df = pd.read_csv(path)

                st.session_state.dataset = df

                st.session_state.dataset_name = (
                    item["name"]
                )

                st.session_state.dataset_path = (
                    str(path)
                )

                st.session_state.dataset_id = (
                    item["id"]
                )

                # Reset automated analysis

                reset_automated_analysis()

                st.session_state.cleaned_dataset = None

                st.session_state.cleaned_dataset_path = None

                st.session_state.generated_chart_config = None
                st.session_state.last_outlier_analysis = None

                st.session_state.ai_insights = None

                st.session_state.agent_result = None

                st.session_state.agent_explanation = None

                save_workspace()

                log_activity(
                    f"Dataset restored: {item['name']}",
                    "Dataset"
                )

                return True

            except Exception:

                return False

    return False


def unload_dataset():

    st.session_state.dataset = None

    st.session_state.dataset_name = None

    st.session_state.dataset_path = None

    st.session_state.dataset_id = None

    # Reset automated analysis

    reset_automated_analysis()

    st.session_state.cleaned_dataset = None

    st.session_state.cleaned_dataset_path = None

    st.session_state.generated_chart_config = None
    st.session_state.last_outlier_analysis = None

    save_workspace()

    log_activity(
        "Dataset unloaded",
        "Dataset"
    )


def delete_dataset(dataset_id):

    for item in st.session_state.dataset_registry:

        if item.get("id") == dataset_id:

            safe_delete_file(
                item.get("path", "")
            )

            break

    st.session_state.dataset_registry = [
        item
        for item in st.session_state.dataset_registry
        if item.get("id") != dataset_id
    ]

    if st.session_state.dataset_id == dataset_id:

        unload_dataset()

    save_workspace()

    log_activity(
        "Dataset deleted from history",
        "Dataset"
    )


# ============================================================
# DATA STATISTICS
# ============================================================

def dataset_statistics(df):

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing": int(
            df.isna().sum().sum()
        ),
        "duplicates": int(
            df.duplicated().sum()
        ),
        "numeric_columns": len(
            df.select_dtypes(
                include=np.number
            ).columns
        ),
        "categorical_columns": len(
            get_categorical_columns(df)
        )
    }


def get_numeric_columns(df):

    return df.select_dtypes(
        include=np.number
    ).columns.tolist()


def get_categorical_columns(df):

    return df.select_dtypes(
        include=["object", "str", "category"]
    ).columns.tolist()


# ============================================================
# AI ENGINE (GROQ CLOUD + LOCAL OLLAMA)
# ============================================================

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"


def get_groq_api_key():
    """Read Groq key safely from Streamlit secrets or environment."""
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "").strip()


def get_groq_response(prompt):
    """Generate a response using Groq Cloud API."""
    api_key = get_groq_api_key()
    if not api_key:
        return ("❌ GROQ_API_KEY missing. Streamlit Cloud → Settings → Secrets "
                "mein GROQ_API_KEY set karein.")

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages":[{"role":"user", "content": str(prompt)}],
                "temperature": 0.2,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as error:
        try:
            detail = response.json().get("error", {}).get("message", str(error))
        except Exception:
            detail = str(error)
        return f"❌ Groq API error: {detail}"
    except requests.exceptions.Timeout:
        return "⏳ Groq response timeout. Please dobara try karein."
    except requests.exceptions.RequestException as error:
        return f"❌ Groq connection error: {error}"
    except (KeyError, IndexError, TypeError, ValueError) as error:
        return f"❌ Groq response parse error: {error}"


def get_ollama_response(prompt):
    """Local Ollama response. Kept available for local AI usage."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return ("❌ Ollama connection nahi ho raha.\n\n"
                "Ollama install aur run karein. Terminal mein `ollama serve` check karein.")
    except requests.exceptions.Timeout:
        return "⏳ AI response timeout. Please dobara try karein."
    except Exception as error:
        return f"AI Error: {error}"


def get_ai_response(prompt):
    """Use Groq when a cloud key is configured; otherwise use local Ollama."""
    if get_groq_api_key():
        return get_groq_response(prompt)
    return get_ollama_response(prompt)


# ============================================================
# AI DATASET CONTEXT
# ============================================================

def create_dataset_context(df):

    try:

        numeric_columns = get_numeric_columns(df)

        summary = (
            df[numeric_columns]
            .describe()
            .round(2)
            .to_string()
            if numeric_columns
            else "No numerical columns"
        )

        return f"""
Dataset Information:

Rows: {len(df)}
Columns: {len(df.columns)}

Column Names:
{list(df.columns)}

Data Types:
{df.dtypes.to_string()}

Missing Values:
{df.isna().sum().to_string()}

Numerical Summary:
{summary}

Sample Data:
{df.head(5).to_string()}
"""

    except Exception:

        return "Dataset loaded."


# ============================================================
# PDF REPORT ENGINE
# ============================================================

def build_pdf_report(df):

    try:

        from reportlab.lib.pagesizes import A4

        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle
        )

        from reportlab.lib import colors

        from reportlab.lib.styles import getSampleStyleSheet

        from reportlab.lib.units import mm

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm
        )

        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph(
                "Analytix AI - Dataset Report",
                styles["Title"]
            )
        )

        elements.append(
            Spacer(1, 15)
        )

        elements.append(
            Paragraph(
                f"Generated: {datetime.now()}",
                styles["Normal"]
            )
        )

        elements.append(
            Spacer(1, 15)
        )

        stats = dataset_statistics(df)

        data = [
            ["Metric", "Value"],
            ["Rows", stats["rows"]],
            ["Columns", stats["columns"]],
            ["Missing Values", stats["missing"]],
            ["Duplicates", stats["duplicates"]],
            ["Numeric Columns", stats["numeric_columns"]],
            ["Categorical Columns", stats["categorical_columns"]]
        ]

        table = Table(
            data,
            colWidths=[80 * mm, 80 * mm]
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.darkblue
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8
                )
            ])
        )

        elements.append(table)

        elements.append(
            Spacer(1, 20)
        )

        elements.append(
            Paragraph(
                "Numerical Statistics",
                styles["Heading2"]
            )
        )

        elements.append(
            Spacer(1, 10)
        )

        numeric_columns = get_numeric_columns(df)

        if numeric_columns:

            summary = (
                df[numeric_columns]
                .describe()
                .round(2)
            )

            summary_data = [
                ["Statistic"] + list(summary.columns)
            ]

            for index, row in summary.iterrows():

                summary_data.append(
                    [str(index)] + [
                        str(value)
                        for value in row.values
                    ]
                )

            summary_table = Table(
                summary_data,
                repeatRows=1
            )

            summary_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.darkblue
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7
                    )
                ])
            )

            elements.append(
                summary_table
            )

        document.build(
            elements
        )

        buffer.seek(0)

        return buffer.getvalue()

    except Exception as error:

        st.error(
            f"PDF Report Error: {error}"
        )

        return None


# ============================================================
# EXCEL REPORT ENGINE
# ============================================================

def build_excel_report(df):

    buffer = BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="Dataset",
            index=False
        )

        numeric_columns = get_numeric_columns(df)

        if numeric_columns:

            df[numeric_columns].describe().to_excel(
                writer,
                sheet_name="Statistics"
            )

        df.isna().sum().to_frame(
            "Missing Values"
        ).to_excel(
            writer,
            sheet_name="Missing Values"
        )

        df.nunique().to_frame(
            "Unique Values"
        ).to_excel(
            writer,
            sheet_name="Unique Values"
        )

    buffer.seek(0)

    return buffer.getvalue()

# ============================================================
# RESET AUTOMATED ANALYSIS
# ============================================================

def reset_automated_analysis():

    st.session_state.automated_analysis = None

    st.session_state.automated_analysis_charts = []

    st.session_state.automated_analysis_dataset_id = None

    st.session_state.automated_analysis_path = None

    st.session_state.agent_result = None

    st.session_state.agent_explanation = None

# ============================================================
# AUTOMATED AI ANALYST ENGINE
# ============================================================

def run_automated_eda(df):

    report = {}

    # --------------------------------------------------------
    # DATASET OVERVIEW
    # --------------------------------------------------------

    report["overview"] = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "memory_usage_mb": round(
            df.memory_usage(deep=True).sum() / (1024 ** 2), 2
        ),
        "duplicate_rows": int(df.duplicated().sum()),
        "total_missing": int(df.isnull().sum().sum())
    }

    # --------------------------------------------------------
    # DATA QUALITY
    # --------------------------------------------------------

    report["missing_values"] = {
        col: int(df[col].isnull().sum())
        for col in df.columns
        if df[col].isnull().sum() > 0
    }

    report["missing_percentage"] = {
        col: round(float(df[col].isnull().mean() * 100), 2)
        for col in df.columns
        if df[col].isnull().sum() > 0
    }

    report["data_types"] = {
        col: str(df[col].dtype)
        for col in df.columns
    }

    report["unique_values"] = {
        col: int(df[col].nunique())
        for col in df.columns
    }

    # --------------------------------------------------------
    # NUMERICAL STATISTICS
    # --------------------------------------------------------

    numeric_df = df.select_dtypes(include=np.number)

    if not numeric_df.empty:

        report["numerical_statistics"] = (
            numeric_df.describe()
            .round(2)
            .to_dict()
        )

    else:

        report["numerical_statistics"] = {}

    # --------------------------------------------------------
    # OUTLIER DETECTION - IQR
    # --------------------------------------------------------

    outlier_report = {}

    for col in numeric_df.columns:

        series = numeric_df[col].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = series[
            (series < lower_bound) |
            (series > upper_bound)
        ]

        outlier_report[col] = {
            "outlier_count": int(len(outliers)),
            "outlier_percentage": round(
                float(len(outliers) / len(series) * 100), 2
            ),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2)
        }

    report["outliers"] = outlier_report

    # --------------------------------------------------------
    # CORRELATION ANALYSIS
    # --------------------------------------------------------

    if len(numeric_df.columns) >= 2:

        report["correlation"] = (
            numeric_df.corr()
            .round(2)
            .to_dict()
        )

    else:

        report["correlation"] = {}

    # --------------------------------------------------------
    # AUTOMATIC BUSINESS INSIGHTS
    # --------------------------------------------------------

    insights = []

    if df.isnull().sum().sum() > 0:

        insights.append(
            f"Dataset contains {int(df.isnull().sum().sum())} missing values. "
            "Consider cleaning them before analysis."
        )

    if df.duplicated().sum() > 0:

        insights.append(
            f"{int(df.duplicated().sum())} duplicate rows detected. "
            "Removing duplicates may improve data quality."
        )

    if not numeric_df.empty:

        for col in numeric_df.columns:

            mean_value = numeric_df[col].mean()
            median_value = numeric_df[col].median()

            if pd.notna(mean_value) and pd.notna(median_value):

                if mean_value > median_value:

                    insights.append(
                        f"{col} may have a right-skewed distribution "
                        "because its mean is greater than its median."
                    )

                elif mean_value < median_value:

                    insights.append(
                        f"{col} may have a left-skewed distribution "
                        "because its mean is lower than its median."
                    )

    if not outlier_report:

        insights.append(
            "Insufficient numerical data for IQR outlier analysis."
        )

    else:

        for col, result in outlier_report.items():

            if result["outlier_count"] > 0:

                insights.append(
                    f"{col} contains {result['outlier_count']} potential "
                    f"outliers ({result['outlier_percentage']}%)."
                )

    report["business_insights"] = insights

    # --------------------------------------------------------
    # DATASET METADATA
    # --------------------------------------------------------

    report["metadata"] = {
        "analysis_timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "dataset_columns": list(df.columns),
        "numeric_columns": list(numeric_df.columns),
        "categorical_columns": list(
            df.select_dtypes(
                include=["object", "category", "string"]
            ).columns
        )
    }

    return report


# ============================================================
# AUTOMATIC CHART GENERATION
# ============================================================

def generate_auto_charts(df):

    charts = []

    numeric_columns = list(
        df.select_dtypes(include=np.number).columns
    )

    categorical_columns = list(
        df.select_dtypes(
            include=["object", "category", "string"]
        ).columns
    )

    # --------------------------------------------------------
    # NUMERICAL DISTRIBUTION CHARTS
    # --------------------------------------------------------

    for col in numeric_columns[:4]:

        try:

            fig, ax = plt.subplots(figsize=(8, 4))

            sns.histplot(
                data=df,
                x=col,
                kde=True,
                ax=ax
            )

            ax.set_title(f"Distribution of {col}")

            ax.set_xlabel(col)

            ax.set_ylabel("Frequency")

            fig.tight_layout()

            charts.append({
                "title": f"Distribution - {col}",
                "figure": fig
            })

        except Exception:

            continue

    # --------------------------------------------------------
    # CATEGORICAL CHARTS
    # --------------------------------------------------------

    for col in categorical_columns[:3]:

        try:

            if df[col].nunique() > 30:
                continue

            fig, ax = plt.subplots(figsize=(8, 4))

            df[col].value_counts().head(10).plot(
                kind="bar",
                ax=ax
            )

            ax.set_title(f"Top Categories - {col}")

            ax.set_xlabel(col)

            ax.set_ylabel("Count")

            plt.xticks(rotation=45)

            fig.tight_layout()

            charts.append({
                "title": f"Category Analysis - {col}",
                "figure": fig
            })

        except Exception:

            continue

    # --------------------------------------------------------
    # CORRELATION HEATMAP
    # --------------------------------------------------------

    if len(numeric_columns) >= 2:

        try:

            fig, ax = plt.subplots(figsize=(10, 6))

            correlation = df[numeric_columns].corr()

            sns.heatmap(
                correlation,
                annot=True,
                cmap="coolwarm",
                fmt=".2f",
                ax=ax
            )

            ax.set_title("Numerical Correlation Heatmap")

            fig.tight_layout()

            charts.append({
                "title": "Correlation Heatmap",
                "figure": fig
            })

        except Exception:

            pass

    return charts


# ============================================================
# AI BUSINESS RECOMMENDATIONS
# ============================================================

def generate_ai_business_recommendations(df, report):

    numeric_summary = report.get(
        "numerical_statistics", {}
    )

    overview = report.get(
        "overview", {}
    )

    insights = report.get(
        "business_insights", []
    )

    prompt = f"""
You are an expert AI Data Analyst and Business Consultant.

Analyze the following dataset summary.

Dataset Overview:
{json.dumps(overview, indent=2)}

Numerical Statistics:
{json.dumps(numeric_summary, indent=2)}

Existing Insights:
{json.dumps(insights, indent=2)}

Provide:

1. Important business insights.
2. Potential business opportunities.
3. Data quality recommendations.
4. Risks and unusual patterns.
5. Actionable recommendations.
6. Suggestions for further analysis.

Be professional, practical, and concise.
Do not invent facts unsupported by the data.
"""

    # Cloud uses Groq when GROQ_API_KEY is configured; local falls back to Ollama.
    return get_ai_response(prompt)


# ============================================================
# SAVE AUTOMATED ANALYSIS
# ============================================================

def save_automated_analysis(report):

    try:

        analysis_id = str(uuid.uuid4())[:8]

        analysis_path = OUTPUTS_DIR / (
            f"automated_analysis_{analysis_id}.json"
        )

        with open(
            analysis_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report,
                f,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        st.session_state.automated_analysis_path = str(
            analysis_path
        )

        # Store the actual report in Workspace preview/content, not only its file path.
        save_output(
            "Automated AI Analysis",
            json.dumps(report, indent=4, ensure_ascii=False, default=str),
            "json"
        )

        log_activity(
            "Automated AI Analysis",
            f"Analysis saved: {analysis_path.name}"
        )

        return str(analysis_path)

    except Exception as e:

        st.error(
            f"Unable to save automated analysis: {e}"
        )

        return None
    
# ============================================================
# AUTONOMOUS ANALYSIS PLANNER + EXECUTOR
# ============================================================

def run_autonomous_analysis(df):
    """Build a transparent analysis plan, execute deterministic checks, and optionally add Ollama narrative."""
    if df is None or df.empty:
        raise ValueError("Please load a non-empty dataset first.")

    numeric_cols = list(df.select_dtypes(include=np.number).columns)
    categorical_cols = list(df.select_dtypes(include=["object", "category", "string", "bool"]).columns)

    plan = [
        "Dataset overview and schema",
        "Missing-value and duplicate audit",
        "Numerical descriptive statistics",
    ]
    if numeric_cols:
        plan += ["IQR-based outlier scan", "Numerical correlation analysis"]
    if categorical_cols:
        plan += ["Top-category frequency analysis"]
    if numeric_cols and categorical_cols:
        plan += ["Compare numeric metrics across categories (available for follow-up)"]

    results = {
        "plan": plan,
        "overview": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "memory_mb": round(float(df.memory_usage(deep=True).sum() / 1024**2), 2),
        },
        "quality": {
            "missing_total": int(df.isna().sum().sum()),
            "missing_by_column": {str(c): int(v) for c, v in df.isna().sum().items() if v},
            "duplicate_rows": int(df.duplicated().sum()),
        },
        "statistics": df[numeric_cols].describe().round(3).to_dict() if numeric_cols else {},
        "outliers": {},
        "correlations": {},
        "top_categories": {},
        "insights": [],
        "ai_summary": "",
    }

    for col in numeric_cols:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) >= 4:
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            count = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
            results["outliers"][str(col)] = {
                "count": count,
                "percentage": round(count / len(series) * 100, 2),
            }
        if len(series):
            mean, median = float(series.mean()), float(series.median())
            if mean > median:
                results["insights"].append(f"{col}: mean ({mean:.3g}) is above median ({median:.3g}); distribution may be right-skewed.")
            elif mean < median:
                results["insights"].append(f"{col}: mean ({mean:.3g}) is below median ({median:.3g}); distribution may be left-skewed.")

    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        results["correlations"] = corr.round(3).to_dict()
        pairs = []
        for i, c1 in enumerate(numeric_cols):
            for c2 in numeric_cols[i+1:]:
                value = corr.loc[c1, c2]
                if pd.notna(value):
                    pairs.append((abs(float(value)), str(c1), str(c2), float(value)))
        for _, c1, c2, value in sorted(pairs, reverse=True)[:5]:
            results["insights"].append(f"Correlation {c1} ↔ {c2}: {value:.3f} (association, not causation).")

    for col in categorical_cols[:5]:
        counts = df[col].astype("string").fillna("(Missing)").value_counts().head(8)
        results["top_categories"][str(col)] = {str(k): int(v) for k, v in counts.items()}

    if results["quality"]["missing_total"]:
        results["insights"].append(f"Data quality: {results['quality']['missing_total']:,} missing cells need review.")
    if results["quality"]["duplicate_rows"]:
        results["insights"].append(f"Data quality: {results['quality']['duplicate_rows']:,} duplicate rows detected.")
    if not results["insights"]:
        results["insights"].append("No prominent heuristic pattern detected; review charts and domain context.")

    # Keep the AI prompt compact and grounded in calculated results.
    ai_payload = {
        "overview": results["overview"],
        "quality": results["quality"],
        "insights": results["insights"],
        "outliers": results["outliers"],
    }
    prompt = (
        "You are Analytix AI, a careful senior data analyst. Explain these computed findings in concise "
        "business-friendly language. Separate observations from recommendations. Do not invent values, "
        "causes, or business context. Mention correlation is not causation.\\n\\n"
        + json.dumps(ai_payload, ensure_ascii=False, default=str)
    )
    results["ai_summary"] = get_ai_response(prompt)
    results["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return results


# ============================================================
# NATURAL LANGUAGE DATA ANALYSIS ENGINE
# ============================================================

def analyze_question(question, df):
    """Deterministic dataset Q&A engine. Returns exact calculations only."""
    import re

    q = str(question).lower().strip()
    if df is None or df.empty:
        return "Dataset is empty. Please load a dataset first."

    numeric = list(df.select_dtypes(include=np.number).columns)
    column = next((c for c in df.columns if str(c).lower() in q), None)
    numeric_column = column if column in numeric else next(
        (c for c in numeric if str(c).lower() in q), None
    )

    # Dataset-level questions
    if re.search(r"\b(rows?|records?|entries)\b|total data", q):
        return f"Total rows: {len(df):,}"
    if re.search(r"\b(columns?|features?)\b", q):
        return f"Total columns: {len(df.columns)}\nColumns: {', '.join(map(str, df.columns))}"
    if "shape" in q or "size of dataset" in q:
        return f"Dataset shape: {df.shape[0]:,} rows × {df.shape[1]:,} columns"
    if any(x in q for x in ["missing", "null", "na values", "null values"]):
        result = df.isna().sum()
        return f"Missing values by column:\n{result.to_string()}\n\nTotal missing cells: {int(result.sum()):,}"
    if "duplicate" in q:
        return f"Duplicate rows: {int(df.duplicated().sum()):,}"
    if any(x in q for x in ["describe", "summary", "statistics", "statistical summary"]):
        return df.describe(include="all").transpose().to_string()
    if "correlation" in q or "correlate" in q:
        return df[numeric].corr().round(4).to_string() if len(numeric) >= 2 else "Correlation needs at least two numeric columns."

    # Column-specific calculations
    if numeric_column is not None:
        series = pd.to_numeric(df[numeric_column], errors="coerce").dropna()
        if series.empty:
            return f"Column '{numeric_column}' has no valid numeric values."
        if any(x in q for x in ["average", "mean", "avg"]):
            return f"Mean of {numeric_column}: {series.mean():,.4f} (n={len(series):,})"
        if "median" in q:
            return f"Median of {numeric_column}: {series.median():,.4f}"
        if "mode" in q:
            modes = series.mode()
            return f"Mode of {numeric_column}: {modes.to_list()}"
        if any(x in q for x in ["standard deviation", "std dev", "stdev"]):
            return f"Standard deviation of {numeric_column}: {series.std():,.4f}"
        if any(x in q for x in ["variance", "var"]):
            return f"Variance of {numeric_column}: {series.var():,.4f}"
        if any(x in q for x in ["maximum", "highest", "largest", " max"]):
            return f"Maximum of {numeric_column}: {series.max():,.4f}"
        if any(x in q for x in ["minimum", "lowest", "smallest", " min"]):
            return f"Minimum of {numeric_column}: {series.min():,.4f}"
        if "sum" in q or "total" in q:
            return f"Sum of {numeric_column}: {series.sum():,.4f}"
        if "count" in q:
            return f"Non-null count of {numeric_column}: {series.count():,}"
        if "unique" in q or "distinct" in q:
            return f"Unique values in {numeric_column}: {series.nunique():,}"

    # Categorical / column-specific questions
    if column is not None:
        if "unique" in q or "distinct" in q:
            return f"Unique values in {column}: {df[column].nunique(dropna=True):,}"
        if any(x in q for x in ["top", "most common", "frequency", "value counts"]):
            return df[column].value_counts(dropna=False).head(10).to_string()
        if "count" in q:
            return f"Non-null count of {column}: {df[column].count():,}"

    # Generic safe results
    if "unique" in q or "distinct" in q:
        return df.nunique(dropna=True).to_string()
    if "count" in q:
        return df.count().to_string()
    return None


# ============================================================
# VISUALIZATION ENGINE
# ============================================================

def automatic_chart_engine(
    df,
    chart_type,
    x_column,
    y_column=None
):

    if chart_type == "Bar":

        fig = px.bar(
            df,
            x=x_column,
            y=y_column,
            title=f"{y_column} by {x_column}"
        )

    elif chart_type == "Line":

        fig = px.line(
            df,
            x=x_column,
            y=y_column,
            title=f"{y_column} Trend"
        )

    elif chart_type == "Scatter":

        fig = px.scatter(
            df,
            x=x_column,
            y=y_column
        )

    elif chart_type == "Pie":

        fig = px.pie(
            df,
            names=x_column,
            values=y_column
        )

    elif chart_type == "Histogram":

        fig = px.histogram(
            df,
            x=x_column
        )

    elif chart_type == "Box":

        fig = px.box(
            df,
            x=x_column,
            y=y_column
        )

    else:

        fig = px.bar(
            df,
            x=x_column,
            y=y_column
        )

    return fig


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

PAGES = [
    "🏠 Dashboard",
    "📊 Data Analysis",
    "🧹 Data Cleaning",
    "📈 Visualization",
    "🔍 Outliers",
    "🧠 AI Insights",
    "🤖 AI Agent",
    "📑 Reports",
    "💾 Saved Workspace"
]

with st.sidebar:

    st.markdown(
        """
        <h1 style="text-align:center;color:#2563eb;">
        🤖 Analytix AI
        </h1>

        <p style="text-align:center;">
        Your Personal AI Data Analyst
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    selected_page = st.radio(
        "🧭 Navigation",
        PAGES,
        key="navigation"
    )

    st.session_state.current_page = (
        selected_page
    )

    st.divider()

    st.markdown(
        "### 📂 Dataset"
    )

    if st.session_state.dataset is not None:

        st.success(
            f"Loaded: {st.session_state.dataset_name}"
        )

        st.caption(
            f"{len(st.session_state.dataset)} Rows | "
            f"{len(st.session_state.dataset.columns)} Columns"
        )

        if st.button(
            "🗑️ Unload Dataset",
            width="stretch"
        ):

            unload_dataset()

            st.rerun()

    else:

        st.info(
            "No dataset loaded."
        )

    st.divider()

    st.caption(
        "Analytix AI | Local Analytics Platform"
    )


# ============================================================
# MAIN CONTENT + RIGHT WORK ACTIVITY
# ============================================================

main_area, activity_area = st.columns(
    [4, 1.25],
    gap="large"
)


# ============================================================
# RIGHT SIDE ACTIVITY PANEL
# ============================================================

with activity_area:

    st.markdown(
        "### ⚡ Work Activity"
    )

    st.caption(
        "Recent operations"
    )

    st.divider()

    if st.session_state.activity:

        for item in st.session_state.activity[:15]:

            with st.container(border=True):

                st.caption(
                    item["time"]
                )

                st.write(
                    item["message"]
                )

                st.caption(
                    item["category"]
                )

    else:

        st.info(
            "No activity yet."
        )

    st.divider()

    st.metric(
        "Saved Outputs",
        len(st.session_state.workspace)
    )

    st.metric(
        "Chat History",
        len(st.session_state.chat_history)
    )

    if st.button(
        "🧹 Clear Activity",
        width="stretch"
    ):

        clear_activity()

        st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

with main_area:

    # ========================================================
    # HEADER
    # ========================================================

    header_html = textwrap.dedent("""
        <div style="background:linear-gradient(135deg,#0f172a,#1d4ed8);padding:28px;border-radius:18px;color:white;text-align:center;margin-bottom:20px;">
            <h1 style="font-size:40px;margin:0 0 8px 0;">🤖 Analytix AI</h1>
            <h3 style="margin:8px 0;">Your Personal AI Data Analyst</h3>
            <p style="margin:10px 0 0;">Analyze • Visualize • Discover • Automate</p>
        </div>
    """).strip()
    st.markdown(header_html, unsafe_allow_html=True)

    # ========================================================
    # DATASET UPLOAD
    # ========================================================

    st.header(
        "📂 Upload Your Dataset"
    )

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel Dataset",
        type=["csv", "xlsx"],
        key="dataset_uploader"
    )

    if uploaded_file is not None:

        # Hash the uploaded bytes so different files with the same name and size
        # are still treated as different datasets. getvalue() doesn't move the cursor.
        upload_bytes = uploaded_file.getvalue()
        upload_signature = hashlib.sha256(upload_bytes).hexdigest()

        if (
            st.session_state.get(
                "_last_upload_signature"
            )
            != upload_signature
        ):

            try:

                df_uploaded = read_dataset(
                    uploaded_file
                )

                if df_uploaded.empty:

                    st.warning(
                        "Uploaded dataset is empty."
                    )

                else:

                    save_dataset(
                        df_uploaded,
                        uploaded_file.name
                    )

                    st.session_state._last_upload_signature = (
                        upload_signature
                    )

                    st.success(
                        "Dataset uploaded and saved successfully!"
                    )

            except Exception as error:

                st.error(
                    f"Upload Error: {error}"
                )

    # ========================================================
    # DATASET RESTORE
    # ========================================================

    if st.session_state.dataset_registry:

        with st.expander(
            "📁 Restore Previous Dataset"
        ):

            dataset_options = {
                (
                    f"{item['name']} | "
                    f"{item['created']}"
                ): item["id"]

                for item in st.session_state.dataset_registry
            }

            selected_dataset = st.selectbox(
                "Select saved dataset",
                list(dataset_options.keys())
            )

            if st.button(
                "Restore Dataset",
                width="stretch"
            ):

                success = restore_dataset(
                    dataset_options[selected_dataset]
                )

                if success:

                    st.success(
                        "Dataset restored successfully."
                    )

                else:

                    st.error(
                        "Dataset restore failed."
                    )

                st.rerun()

    # ========================================================
    # DATASET PREVIEW
    # ========================================================

    df = st.session_state.dataset

    if df is not None:

        st.divider()

        st.subheader(
            "📋 Dataset Preview"
        )

        st.dataframe(
            df.head(100),
            width="stretch"
        )

        stats = dataset_statistics(
            df
        )

        numeric_columns = get_numeric_columns(
            df
        )

        categorical_columns = get_categorical_columns(
            df
        )

        # ====================================================
        # DASHBOARD
        # ====================================================

        if selected_page == "🏠 Dashboard":

            st.header(
                "📊 Dashboard Overview"
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Rows",
                stats["rows"]
            )

            col2.metric(
                "Columns",
                stats["columns"]
            )

            col3.metric(
                "Missing Values",
                stats["missing"]
            )

            col4.metric(
                "Duplicates",
                stats["duplicates"]
            )

            st.divider()

            st.subheader(
                "📈 Dataset Overview"
            )

            if numeric_columns:

                st.dataframe(
                    df[numeric_columns].describe(),
                    width="stretch"
                )

            st.subheader(
                "🧩 Column Information"
            )

            column_info = pd.DataFrame({
                "Column": df.columns,
                "Data Type": df.dtypes.astype(str).values,
                "Missing Values": df.isna().sum().values,
                "Unique Values": df.nunique().values
            })

            st.dataframe(
                column_info,
                width="stretch"
            )

            st.subheader(
                "💡 Quick Insights"
            )

            st.write(
                f"• Dataset contains {stats['rows']} records."
            )

            st.write(
                f"• Total {stats['columns']} columns available."
            )

            st.write(
                f"• {stats['missing']} missing values detected."
            )

            st.write(
                f"• {stats['duplicates']} duplicate records found."
            )

            st.write(
                f"• {stats['numeric_columns']} numerical columns."
            )

            st.write(
                f"• {stats['categorical_columns']} categorical columns."
            )

        # ====================================================
        # DATA ANALYSIS
        # ====================================================

        elif selected_page == "📊 Data Analysis":

            st.header(
                "📊 Data Analysis"
            )

            if numeric_columns:

                selected_column = st.selectbox(
                    "Select numerical column",
                    numeric_columns,
                    key="analysis_column"
                )

                series = df[selected_column]

                st.subheader(
                    "Statistical Analysis"
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Mean",
                    round(series.mean(), 3)
                )

                col2.metric(
                    "Median",
                    round(series.median(), 3)
                )

                col3.metric(
                    "Std",
                    round(series.std(), 3)
                )

                col4.metric(
                    "Maximum",
                    series.max()
                )

                st.divider()

                st.subheader(
                    "📉 Distribution"
                )

                fig, ax = plt.subplots()

                sns.histplot(
                    series.dropna(),
                    kde=True,
                    ax=ax
                )

                ax.set_title(
                    f"Distribution of {selected_column}"
                )

                st.pyplot(fig)

                plt.close(fig)

                st.subheader(
                    "Correlation Matrix"
                )

                if len(numeric_columns) > 1:

                    fig, ax = plt.subplots(
                        figsize=(10, 6)
                    )

                    sns.heatmap(
                        df[numeric_columns].corr(),
                        annot=True,
                        cmap="coolwarm",
                        ax=ax
                    )

                    st.pyplot(fig)

                    plt.close(fig)

            else:

                st.warning(
                    "No numerical columns found."
                )

        # ====================================================
        # DATA CLEANING
        # ====================================================

        elif selected_page == "🧹 Data Cleaning":

            st.header(
                "🧹 Data Cleaning Studio"
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Missing Values",
                stats["missing"]
            )

            col2.metric(
                "Duplicate Rows",
                stats["duplicates"]
            )

            st.divider()

            cleaning_action = st.selectbox(
                "Select Cleaning Operation",
                [
                    "Remove Duplicate Rows",
                    "Remove Missing Rows",
                    "Fill Missing Values",
                    "Replace Missing Values with 0"
                ],
                key="cleaning_action"
            )

            if st.button(
                "🚀 Execute Cleaning",
                width="stretch"
            ):

                cleaned = df.copy()

                try:

                    if cleaning_action == "Remove Duplicate Rows":

                        cleaned = cleaned.drop_duplicates()

                    elif cleaning_action == "Remove Missing Rows":

                        cleaned = cleaned.dropna()

                    elif cleaning_action == "Fill Missing Values":

                        for column in cleaned.columns:

                            if cleaned[column].dtype.kind in "biufc":

                                median_value = cleaned[column].median()

                                cleaned[column] = cleaned[column].fillna(
                                    median_value
                                )

                            else:

                                mode_values = cleaned[column].mode()

                                fill_value = (
                                    mode_values.iloc[0]
                                    if not mode_values.empty
                                    else "Unknown"
                                )

                                cleaned[column] = cleaned[column].fillna(
                                    fill_value
                                )

                    elif cleaning_action == "Replace Missing Values with 0":

                        cleaned = cleaned.fillna(0)

                    cleaned_path = DATASETS_DIR / (
                        f"cleaned_{st.session_state.dataset_id}.csv"
                    )

                    cleaned.to_csv(
                        cleaned_path,
                        index=False
                    )

                    st.session_state.cleaned_dataset = (
                        cleaned
                    )

                    st.session_state.cleaned_dataset_path = (
                        str(cleaned_path)
                    )

                    save_output(
                        "Cleaned Dataset",
                        f"Cleaning Operation: {cleaning_action}\n"
                        f"Original Rows: {len(df)}\n"
                        f"Cleaned Rows: {len(cleaned)}\n"
                        f"Remaining Missing Values: "
                        f"{cleaned.isna().sum().sum()}",
                        "Cleaning"
                    )

                    log_activity(
                        f"Dataset cleaned: {cleaning_action}",
                        "Cleaning"
                    )

                    st.success(
                        "Cleaning completed successfully!"
                    )

                except Exception as error:

                    st.error(
                        f"Cleaning Error: {error}"
                    )

            if st.session_state.cleaned_dataset is not None:

                st.subheader(
                    "Cleaned Dataset Preview"
                )

                st.dataframe(
                    st.session_state.cleaned_dataset.head(100),
                    width="stretch"
                )

                st.download_button(
                    "⬇️ Download Cleaned CSV",
                    data=st.session_state.cleaned_dataset.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="cleaned_dataset.csv",
                    mime="text/csv",
                    width="stretch"
                )

        # ====================================================
        # VISUALIZATION
        # ====================================================

        elif selected_page == "📈 Visualization":

            st.header("📈 Visualization Studio")

            chart_type = st.selectbox(
                "Select Chart Type",
                ["Bar", "Line", "Scatter", "Pie", "Histogram", "Box"],
                key="chart_type"
            )

            x_column = st.selectbox(
                "X Axis / Category", df.columns, key="chart_x"
            )

            y_column = None
            if chart_type != "Histogram":
                y_column = st.selectbox(
                    "Y Axis / Values",
                    df.columns,
                    index=(1 if len(df.columns) > 1 else 0),
                    key="chart_y"
                )

            if st.button("Generate Chart", width="stretch", key="generate_chart_button"):
                st.session_state.generated_chart_config = {
                    "dataset_id": st.session_state.dataset_id,
                    "chart_type": chart_type,
                    "x_column": x_column,
                    "y_column": y_column,
                }

            # Render the last generated chart whenever this page is revisited.
            chart_config = st.session_state.generated_chart_config
            if chart_config and chart_config.get("dataset_id") == st.session_state.dataset_id:
                try:
                    fig = automatic_chart_engine(
                        df,
                        chart_config["chart_type"],
                        chart_config["x_column"],
                        chart_config.get("y_column")
                    )
                    st.plotly_chart(fig, width="stretch", key="persistent_generated_chart")

                    chart_path = CHARTS_DIR / (
                        f"{st.session_state.dataset_id}_{chart_config['chart_type'].lower()}_latest.html"
                    )
                    fig.write_html(str(chart_path))

                    st.download_button(
                        "⬇️ Download Current Chart (HTML)",
                        data=fig.to_html(include_plotlyjs="cdn"),
                        file_name=f"analytix_ai_{chart_config['chart_type'].lower()}.html",
                        mime="text/html",
                        key="persistent_chart_download",
                        width="stretch"
                    )
                    plt.close("all")
                except Exception as error:
                    st.error(f"Chart Error: {error}")
            else:
                st.info("Choose chart settings and click Generate Chart. Your generated chart will remain available when you return to this section.")

        # ====================================================
        # OUTLIERS
        # ====================================================

        elif selected_page == "🔍 Outliers":

            st.header(
                "🔍 Outlier Detection Engine"
            )

            if numeric_columns:

                outlier_column = st.selectbox(
                    "Select Numerical Column",
                    numeric_columns,
                    key="outlier_column"
                )

                series = df[outlier_column].dropna()

                q1 = series.quantile(0.25)

                q3 = series.quantile(0.75)

                iqr = q3 - q1

                lower_bound = q1 - 1.5 * iqr

                upper_bound = q3 + 1.5 * iqr

                outliers = df[
                    (
                        df[outlier_column] < lower_bound
                    )
                    |
                    (
                        df[outlier_column] > upper_bound
                    )
                ]

                st.session_state.last_outlier_analysis = {
                    "dataset_id": st.session_state.dataset_id,
                    "column": outlier_column,
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "count": int(len(outliers)),
                    "records": outliers.copy(),
                }

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Outliers",
                    len(outliers)
                )

                col2.metric(
                    "Lower Bound",
                    round(lower_bound, 3)
                )

                col3.metric(
                    "Upper Bound",
                    round(upper_bound, 3)
                )

                fig, ax = plt.subplots()

                sns.boxplot(
                    x=df[outlier_column],
                    ax=ax
                )

                st.pyplot(fig)

                plt.close(fig)

                st.subheader(
                    "Detected Outlier Records"
                )

                st.dataframe(
                    outliers,
                    width="stretch"
                )

                if st.button(
                    "Save Outlier Analysis"
                ):

                    save_output(
                        f"Outliers - {outlier_column}",
                        outliers.to_string(),
                        "Outliers"
                    )

                    st.success(
                        "Outlier analysis saved!"
                    )

            else:

                st.warning(
                    "No numerical columns available."
                )

        # ====================================================
        # AI INSIGHTS
        # ====================================================

        elif selected_page == "🧠 AI Insights":

            st.header(
                "🧠 AI Insights Engine"
            )

            st.write(
                "Generate AI-powered analysis of your dataset."
            )

            if st.button(
                "Generate AI Insights",
                width="stretch"
            ):

                with st.spinner(
                    "AI is analyzing your dataset..."
                ):

                    context = create_dataset_context(
                        df
                    )

                    prompt = f"""
You are a professional Data Analyst.

Analyze the following dataset and provide:

1. Important patterns
2. Key business insights
3. Data quality issues
4. Interesting trends
5. Actionable recommendations

Dataset:
{context}
"""

                    response = get_ai_response(
                        prompt
                    )

                    st.session_state.ai_insights = (
                        response
                    )

                    save_output(
                        "AI Dataset Insights",
                        response,
                        "AI Insights"
                    )

                    log_activity(
                        "AI insights generated",
                        "AI Insights"
                    )

            if st.session_state.ai_insights:

                st.subheader(
                    "AI Analysis Results"
                )

                st.markdown(
                    st.session_state.ai_insights
                )

        # ====================================================
        # AI AGENT
        # ====================================================

        elif selected_page == "🤖 AI Agent":

            st.header("🤖 Automated AI Analyst")

            st.markdown("""
            Complete dataset analysis, data quality monitoring,
            automatic charts, business insights and AI recommendations.
            """)

            # AUTONOMOUS ANALYST
            st.divider()
            st.subheader("🧭 Autonomous AI Analyst")
            st.caption("AI creates a data-driven plan, runs deterministic checks, and summarizes calculated findings.")
            if st.button("🚀 Run Autonomous Analysis", key="run_autonomous_analysis", type="primary", use_container_width=True):
                with st.spinner("Planning and executing dataset analysis..."):
                    try:
                        autonomous_result = run_autonomous_analysis(df)
                        st.session_state.autonomous_analysis = {
                            "dataset_id": st.session_state.dataset_id,
                            "result": autonomous_result,
                        }
                        save_output(
                            "Autonomous AI Analysis",
                            json.dumps(autonomous_result, indent=2, ensure_ascii=False, default=str),
                            "AI Agent",
                        )
                        log_activity("Autonomous AI analysis completed", "AI Agent")
                        st.success("Autonomous analysis completed.")
                    except Exception as exc:
                        st.error(f"Autonomous analysis failed: {exc}")

            saved_autonomous = st.session_state.get("autonomous_analysis")
            if saved_autonomous and saved_autonomous.get("dataset_id") == st.session_state.dataset_id:
                auto = saved_autonomous["result"]
                with st.expander("📋 Analysis Plan", expanded=True):
                    for step_no, step in enumerate(auto.get("plan", []), start=1):
                        st.write(f"{step_no}. {step}")
                overview = auto.get("overview", {})
                m1, m2, m3 = st.columns(3)
                m1.metric("Rows", overview.get("rows", 0))
                m2.metric("Columns", overview.get("columns", 0))
                m3.metric("Memory (MB)", overview.get("memory_mb", 0))
                st.markdown("#### 🧹 Data Quality")
                st.write(f"Missing cells: **{auto.get('quality', {}).get('missing_total', 0):,}**")
                st.write(f"Duplicate rows: **{auto.get('quality', {}).get('duplicate_rows', 0):,}**")
                if auto.get("quality", {}).get("missing_by_column"):
                    st.dataframe(pd.DataFrame(
                        list(auto["quality"]["missing_by_column"].items()),
                        columns=["Column", "Missing values"]
                    ), use_container_width=True)
                st.markdown("#### 💡 Calculated Insights")
                for insight in auto.get("insights", []):
                    st.write(f"• {insight}")
                st.markdown("#### 🧠 AI Summary")
                st.markdown(auto.get("ai_summary") or "AI summary unavailable; calculated results are shown above.")
                if auto.get("statistics"):
                    with st.expander("📊 Numerical statistics"):
                        st.json(auto["statistics"])
                if auto.get("outliers"):
                    with st.expander("🔎 Outlier scan"):
                        st.dataframe(pd.DataFrame(auto["outliers"]).T, use_container_width=True)
                if auto.get("correlations"):
                    with st.expander("🔗 Correlation matrix"):
                        st.dataframe(pd.DataFrame(auto["correlations"]), use_container_width=True)
                if auto.get("top_categories"):
                    with st.expander("🏷️ Top categories"):
                        for col_name, values in auto["top_categories"].items():
                            st.write(f"**{col_name}**")
                            st.dataframe(pd.DataFrame(values.items(), columns=["Category", "Count"]), use_container_width=True)

            # ====================================================
            # ANALYSIS CONTROLS
            # ====================================================

            st.divider()

            st.subheader("🚀 Automated Analysis")

            col1, col2 = st.columns(2)

            with col1:

                run_eda = st.button(
                    "🔍 Run Complete Analysis",
                    use_container_width=True,
                    type="primary"
                )

            with col2:

                generate_recommendations = st.button(
                    "🧠 Generate AI Recommendations",
                    use_container_width=True
                )

            # ====================================================
            # RUN AUTOMATED EDA
            # ====================================================

            if run_eda:

                with st.spinner(
                    "Analyzing dataset... Please wait."
                ):

                    try:

                        report = run_automated_eda(df)

                        charts = generate_auto_charts(df)

                        st.session_state.automated_analysis = report

                        st.session_state.automated_analysis_charts = charts

                        st.session_state.automated_analysis_dataset_id = (
                            st.session_state.dataset_id
                        )

                        st.session_state.automated_analysis_path = None

                        log_activity(
                            "Automated EDA",
                            "Complete automated analysis generated."
                        )

                        st.success(
                            "Dataset analysis completed successfully!"
                        )

                    except Exception as e:

                        st.error(
                            f"Analysis Error: {str(e)}"
                        )

            # ====================================================
            # GENERATE AI RECOMMENDATIONS
            # ====================================================

            if generate_recommendations:

                current_report = (
                    st.session_state.automated_analysis
                )

                if (
                    current_report is None
                    or st.session_state.automated_analysis_dataset_id
                    != st.session_state.dataset_id
                ):

                    with st.spinner(
                        "Preparing dataset analysis..."
                    ):

                        current_report = run_automated_eda(df)

                        charts = generate_auto_charts(df)

                        st.session_state.automated_analysis = (
                            current_report
                        )

                        st.session_state.automated_analysis_charts = (
                            charts
                        )

                        st.session_state.automated_analysis_dataset_id = (
                            st.session_state.dataset_id
                        )

                with st.spinner(
                    "Generating recommendations using Ollama..."
                ):

                    try:

                        recommendations = (
                            generate_ai_business_recommendations(
                                df,
                                current_report
                            )
                        )

                        current_report["ai_recommendations"] = (
                            recommendations
                        )

                        st.session_state.automated_analysis = (
                            current_report
                        )

                        log_activity(
                            "AI Recommendations",
                            "AI business recommendations generated."
                        )

                        st.success(
                            "AI recommendations generated successfully!"
                        )

                    except Exception as e:

                        st.error(
                            f"Recommendation Error: {str(e)}"
                        )

            # ====================================================
            # DISPLAY ANALYSIS
            # ====================================================

            report = (
                st.session_state.automated_analysis
            )

            report_dataset_id = (
                st.session_state.automated_analysis_dataset_id
            )

            if (
                report is not None
                and report_dataset_id == st.session_state.dataset_id
            ):

                overview = report.get(
                    "overview", {}
                )

                metadata = report.get(
                    "metadata", {}
                )

                # ====================================================
                # DATASET INFORMATION
                # ====================================================

                st.divider()

                st.subheader("📊 Dataset Overview")

                st.caption(
                    f"Dataset: {st.session_state.dataset_name}"
                )

                st.caption(
                    f"Analysis Time: "
                    f"{metadata.get('analysis_timestamp', 'N/A')}"
                )

                # ====================================================
                # KPI CARDS
                # ====================================================

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Total Rows",
                    f"{overview.get('rows', 0):,}"
                )

                c2.metric(
                    "Total Columns",
                    overview.get("columns", 0)
                )

                c3.metric(
                    "Missing Values",
                    overview.get("total_missing", 0)
                )

                c4.metric(
                    "Duplicate Rows",
                    overview.get("duplicate_rows", 0)
                )

                st.caption(
                    f"Memory Usage: "
                    f"{overview.get('memory_usage_mb', 0)} MB"
                )

                # ====================================================
                # PROFESSIONAL TABS
                # ====================================================

                (
                    tab_overview,
                    tab_quality,
                    tab_statistics,
                    tab_charts,
                    tab_insights,
                    tab_ai
                ) = st.tabs([
                    "📊 Overview",
                    "🧹 Data Quality",
                    "📈 Statistics",
                    "📉 Charts",
                    "💡 Insights",
                    "🤖 AI Recommendations"
                ])

                # ====================================================
                # TAB 1 - OVERVIEW
                # ====================================================

                with tab_overview:

                    st.subheader("Dataset Information")

                    st.write(
                        f"**Rows:** {overview.get('rows', 0):,}"
                    )

                    st.write(
                        f"**Columns:** {overview.get('columns', 0)}"
                    )

                    st.write(
                        f"**Missing Values:** "
                        f"{overview.get('total_missing', 0)}"
                    )

                    st.write(
                        f"**Duplicate Rows:** "
                        f"{overview.get('duplicate_rows', 0)}"
                    )

                    st.write(
                        f"**Memory Usage:** "
                        f"{overview.get('memory_usage_mb', 0)} MB"
                    )

                    st.subheader("Dataset Metadata")

                    st.json(
                        metadata,
                        expanded=False
                    )

                # ====================================================
                # TAB 2 - DATA QUALITY
                # ====================================================

                with tab_quality:

                    st.subheader("🧹 Missing Values")

                    missing_values = report.get(
                        "missing_values", {}
                    )

                    missing_percentage = report.get(
                        "missing_percentage", {}
                    )

                    if missing_values:

                        missing_df = pd.DataFrame({
                            "Column": list(
                                missing_values.keys()
                            ),

                            "Missing Count": list(
                                missing_values.values()
                            ),

                            "Missing Percentage": [
                                missing_percentage.get(
                                    col, 0
                                )
                                for col in missing_values.keys()
                            ]
                        })

                        st.dataframe(
                            missing_df,
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.success(
                            "No missing values detected."
                        )

                    st.subheader("Column Information")

                    data_types = report.get(
                        "data_types", {}
                    )

                    unique_values = report.get(
                        "unique_values", {}
                    )

                    column_info = pd.DataFrame({
                        "Column": list(data_types.keys()),

                        "Data Type": list(data_types.values()),

                        "Unique Values": [
                            unique_values.get(col, 0)
                            for col in data_types.keys()
                        ]
                    })

                    st.dataframe(
                        column_info,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.subheader("Duplicate Analysis")

                    st.metric(
                        "Duplicate Rows",
                        overview.get("duplicate_rows", 0)
                    )

                # ====================================================
                # TAB 3 - STATISTICS
                # ====================================================

                with tab_statistics:

                    st.subheader(
                        "📈 Numerical Statistics"
                    )

                    numerical_stats = report.get(
                        "numerical_statistics", {}
                    )

                    if numerical_stats:

                        stats_df = pd.DataFrame(
                            numerical_stats
                        )

                        st.dataframe(
                            stats_df,
                            use_container_width=True
                        )

                    else:

                        st.info(
                            "No numerical columns available."
                        )

                    st.subheader(
                        "🔍 Outlier Analysis"
                    )

                    outliers = report.get(
                        "outliers", {}
                    )

                    if outliers:

                        outlier_df = pd.DataFrame(
                            outliers
                        ).T

                        outlier_df.index.name = "Column"

                        st.dataframe(
                            outlier_df,
                            use_container_width=True
                        )

                    else:

                        st.info(
                            "No outlier analysis available."
                        )

                # ====================================================
                # TAB 4 - CHARTS
                # ====================================================

                with tab_charts:

                    st.subheader(
                        "📊 Automatic Visualizations"
                    )

                    charts = (
                        st.session_state.automated_analysis_charts
                    )

                    if charts:

                        for chart in charts:

                            st.markdown(
                                f"### {chart['title']}"
                            )

                            st.pyplot(
                                chart["figure"],
                                use_container_width=True
                            )

                    else:

                        st.info(
                            "Run complete analysis to generate charts."
                        )

                # ====================================================
                # TAB 5 - INSIGHTS
                # ====================================================

                with tab_insights:

                    st.subheader(
                        "💡 Automatic Business Insights"
                    )

                    insights = report.get(
                        "business_insights", []
                    )

                    if insights:

                        for index, insight in enumerate(
                            insights,
                            start=1
                        ):

                            st.info(
                                f"**Insight {index}:** {insight}"
                            )

                    else:

                        st.info(
                            "No automatic insights available."
                        )

                    st.subheader(
                        "🔗 Correlation Analysis"
                    )

                    correlation = report.get(
                        "correlation", {}
                    )

                    if correlation:

                        correlation_df = pd.DataFrame(
                            correlation
                        )

                        st.dataframe(
                            correlation_df,
                            use_container_width=True
                        )

                    else:

                        st.info(
                            "Correlation requires at least "
                            "two numerical columns."
                        )

                # ====================================================
                # TAB 6 - AI RECOMMENDATIONS
                # ====================================================

                with tab_ai:

                    st.subheader(
                        "🤖 AI Business Recommendations"
                    )

                    recommendations = report.get(
                        "ai_recommendations"
                    )

                    if recommendations:

                        st.markdown(
                            recommendations
                        )

                    else:

                        st.info(
                            "Click Generate AI Recommendations "
                            "to generate recommendations."
                        )

                # ====================================================
                # SAVE AND EXPORT
                # ====================================================

                st.divider()

                st.header(
                    "💾 Save & Export Analysis"
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "💾 Save Analysis",
                        key="save_automated_analysis",
                        use_container_width=True
                    ):

                        saved_path = (
                            save_automated_analysis(
                                report
                            )
                        )

                        if saved_path:

                            st.success(
                                "Analysis saved successfully!"
                            )

                            st.code(
                                saved_path
                            )

                with col2:

                    json_data = json.dumps(
                        report,
                        indent=4,
                        ensure_ascii=False,
                        default=str
                    )

                    st.download_button(
                        "📥 Download Analysis JSON",
                        data=json_data,
                        file_name="analytix_ai_analysis.json",
                        mime="application/json",
                        key="download_automated_analysis",
                        use_container_width=True
                    )

            elif report is not None:

                st.warning(
                    "Analysis belongs to another dataset. "
                    "Please run analysis again."
                )

            else:

                st.info(
                    "👆 Click Run Complete Analysis to begin."
                )

            # ====================================================
            # NATURAL LANGUAGE AI AGENT
            # ====================================================

            st.divider()

            st.header(
                "💬 Ask Your Data"
            )

            st.write(
                "Ask questions about your dataset in natural language."
            )

            agent_question = st.text_input(
                "Ask your question",
                placeholder="Example: What is the average sales?",
                key="agent_question"
            )

            if st.button(
                "🤖 Run AI Agent",
                key="run_natural_language_agent",
                use_container_width=True
            ):

                if agent_question.strip():

                    with st.spinner(
                        "AI Agent is analyzing your question..."
                    ):

                        try:

                            result = analyze_question(
                                agent_question,
                                df
                            )

                            if result is not None:

                                st.session_state.agent_result = (
                                    result
                                )

                                st.session_state.agent_explanation = (
                                    None
                                )

                                save_output(
                                    "AI Agent Result",
                                    f"Question: {agent_question}\n\n"
                                    f"Result:\n{result}",
                                    "AI Agent"
                                )

                            else:

                                context = create_dataset_context(
                                    df
                                )

                                prompt = f"""
You are Analytix AI, an expert data analyst.

Dataset:
{context}

User Question:
{agent_question}

Explain how to answer this question using the dataset.
Do not invent numerical results.
"""

                                explanation = (
                                    get_ai_response(
                                        prompt
                                    )
                                )

                                st.session_state.agent_result = (
                                    "No direct calculation available."
                                )

                                st.session_state.agent_explanation = (
                                    explanation
                                )

                                save_output(
                                    "AI Agent Explanation",
                                    explanation,
                                    "AI Agent"
                                )

                            save_chat(
                                agent_question,
                                str(
                                    st.session_state.agent_result
                                )
                                + "\n\n"
                                + str(
                                    st.session_state.agent_explanation
                                    or ""
                                )
                            )

                            log_activity(
                                "AI Agent completed query",
                                "AI Agent"
                            )

                        except Exception as e:

                            st.error(
                                f"AI Agent Error: {str(e)}"
                            )

                else:

                    st.warning(
                        "Please enter a question first."
                    )

            # ====================================================
            # DISPLAY AI AGENT RESULT
            # ====================================================

            if st.session_state.agent_result is not None:

                st.subheader(
                    "📌 Agent Result"
                )

                st.write(
                    st.session_state.agent_result
                )

            if st.session_state.agent_explanation:

                st.subheader(
                    "🧠 AI Explanation"
                )

                st.markdown(
                    st.session_state.agent_explanation
                )
                
        # ====================================================
        # REPORTS
        # ====================================================

        elif selected_page == "📑 Reports":

            st.header(
                "📑 Report Generator"
            )

            st.write(
                "Generate professional dataset reports."
            )

            report_name = st.text_input(
                "Report Name",
                value="Analytix_AI_Report"
            )

            report_name = safe_filename(
                report_name
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Generate Excel Report",
                    width="stretch"
                ):

                    try:

                        excel_data = build_excel_report(
                            df
                        )

                        report_path = REPORTS_DIR / (
                            f"{report_name}.xlsx"
                        )

                        with open(
                            report_path,
                            "wb"
                        ) as file:

                            file.write(
                                excel_data
                            )

                        log_activity(
                            "Excel report generated",
                            "Reports"
                        )

                        st.download_button(
                            "⬇️ Download Excel",
                            data=excel_data,
                            file_name=f"{report_name}.xlsx",
                            mime=(
                                "application/vnd.openxmlformats-officedocument."
                                "spreadsheetml.sheet"
                            ),
                            width="stretch"
                        )

                    except Exception as error:

                        st.error(
                            f"Excel Report Error: {error}"
                        )

            with col2:

                if st.button(
                    "Generate PDF Report",
                    width="stretch"
                ):

                    pdf_data = build_pdf_report(
                        df
                    )

                    if pdf_data:

                        report_path = REPORTS_DIR / (
                            f"{report_name}.pdf"
                        )

                        with open(
                            report_path,
                            "wb"
                        ) as file:

                            file.write(
                                pdf_data
                            )

                        log_activity(
                            "PDF report generated",
                            "Reports"
                        )

                        st.download_button(
                            "⬇️ Download PDF",
                            data=pdf_data,
                            file_name=f"{report_name}.pdf",
                            mime="application/pdf",
                            width="stretch"
                        )

        # ====================================================
        # SAVED WORKSPACE
        # ====================================================

        elif selected_page == "💾 Saved Workspace":

            st.header(
                "💾 Saved Workspace"
            )

            st.write(
                "Your saved outputs, analyses, and conversations."
            )

            st.divider()

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Saved Outputs",
                len(st.session_state.workspace)
            )

            col2.metric(
                "Saved Chats",
                len(st.session_state.chat_history)
            )

            col3.metric(
                "Datasets",
                len(st.session_state.dataset_registry)
            )

            st.divider()

            # SAVED OUTPUTS

            st.subheader(
                "📦 Saved Outputs"
            )

            if st.session_state.workspace:

                if st.button(
                    "🗑️ Clear All Saved Outputs",
                    type="secondary"
                ):

                    clear_workspace()

                    st.rerun()

                for item in st.session_state.workspace:

                    with st.container(border=True):

                        col1, col2 = st.columns(
                            [4, 1]
                        )

                        with col1:

                            st.markdown(
                                f"### {item['title']}"
                            )

                            st.caption(
                                f"{item['category']} | "
                                f"{item['created']}"
                            )

                        with col2:

                            if st.button(
                                "🗑️",
                                key=f"delete_{item['id']}"
                            ):

                                delete_output(
                                    item["id"]
                                )

                                st.rerun()

                        path = Path(
                            item["path"]
                        )

                        if path.exists():

                            with open(
                                path,
                                "r",
                                encoding="utf-8"
                            ) as file:

                                content = file.read()

                            with st.expander(
                                "View Saved Result"
                            ):

                                st.text(
                                    content
                                )

                                st.download_button(
                                    "Download Output",
                                    data=content,
                                    file_name=(
                                        safe_filename(
                                            item["title"]
                                        )
                                        + ".txt"
                                    ),
                                    key=f"download_{item['id']}"
                                )

            else:

                st.info(
                    "No saved outputs yet."
                )

            st.divider()

            # CHAT HISTORY

            st.subheader(
                "💬 Chat History"
            )

            if st.session_state.chat_history:

                if st.button(
                    "🗑️ Clear All Chats"
                ):

                    clear_chat_history()

                    st.rerun()

                for chat in st.session_state.chat_history:

                    with st.container(border=True):

                        col1, col2 = st.columns(
                            [4, 1]
                        )

                        with col1:

                            st.caption(
                                chat["created"]
                            )

                            st.markdown(
                                f"**Q:** {chat['question']}"
                            )

                        with col2:

                            if st.button(
                                "🗑️",
                                key=f"chat_delete_{chat['id']}"
                            ):

                                delete_chat(
                                    chat["id"]
                                )

                                st.rerun()

                        with st.expander(
                            "View Answer"
                        ):

                            st.write(
                                chat["answer"]
                            )

            else:

                st.info(
                    "No saved conversations."
                )

            st.divider()

            # DATASET HISTORY

            st.subheader(
                "📁 Dataset History"
            )

            for item in st.session_state.dataset_registry:

                with st.container(border=True):

                    st.markdown(
                        f"**{item['name']}**"
                    )

                    st.caption(
                        f"{item['rows']} Rows | "
                        f"{item['columns']} Columns"
                    )

                    st.caption(
                        f"Uploaded: {item['created']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Restore",
                            key=f"restore_{item['id']}"
                        ):

                            restore_dataset(
                                item["id"]
                            )

                            st.rerun()

                    with col2:

                        if st.button(
                            "Delete",
                            key=f"dataset_delete_{item['id']}"
                        ):

                            delete_dataset(
                                item["id"]
                            )

                            st.rerun()

    else:

        st.warning(
            "Please upload or restore a dataset first."
        )

    # ========================================================
    # ASK YOUR DATA
    # ========================================================

    if df is not None:

        st.divider()

        st.header(
            "💬 Ask Your Data"
        )

        with st.expander(
            "Ask questions about your dataset",
            expanded=False
        ):

            ask_question = st.text_input(
                "Enter your question",
                key="ask_data_question",
                placeholder="Example: Show missing values"
            )

            if st.button(
                "🔎 Analyze Question",
                key="ask_data_button"
            ):

                if ask_question:

                    result = analyze_question(
                        ask_question,
                        df
                    )

                    if result is not None:

                        st.success(
                            "Analysis completed"
                        )

                        st.write(
                            result
                        )

                        save_chat(
                            ask_question,
                            str(result)
                        )

                        log_activity(
                            "Ask Your Data query completed",
                            "Data Analysis"
                        )

                    else:

                        st.info(
                            "Question requires AI analysis."
                        )

                        with st.spinner(
                            "AI is analyzing your question..."
                        ):

                            context = create_dataset_context(
                                df
                            )

                            prompt = f"""
You are a professional data analyst.

Dataset:
{context}

Question:
{ask_question}

Provide a useful analytical answer.
Do not invent exact numbers.
"""

                            response = get_ai_response(
                                prompt
                            )

                            st.markdown(
                                response
                            )

                            save_chat(
                                ask_question,
                                response
                            )

                            log_activity(
                                "AI question answered",
                                "AI"
                            )

        # ====================================================
        # LOCAL AI ANALYST
        # ====================================================

        with st.expander(
            "🧠 Local AI Analyst",
            expanded=False
        ):

            st.caption(
                "Cloud app: Groq AI • Local app: Ollama"
            )

            ai_question = st.text_area(
                "Ask AI Analyst",
                key="local_ai_question",
                placeholder=(
                    "Explain my dataset, identify trends, "
                    "suggest business insights..."
                )
            )

            if st.button(
                "Generate AI Response",
                key="local_ai_button"
            ):

                if ai_question:

                    with st.spinner(
                        "AI is thinking..."
                    ):

                        context = create_dataset_context(
                            df
                        )

                        prompt = f"""
You are Analytix AI.

Analyze this dataset carefully.

Dataset:
{context}

User Question:
{ai_question}

Provide a professional answer.
Mention limitations if relevant.
"""

                        response = get_ollama_response(
                            prompt
                        )

                        st.markdown(
                            response
                        )

                        save_chat(
                            ai_question,
                            response
                        )

                        save_output(
                            "Local AI Analyst",
                            response,
                            "AI Analyst"
                        )

                        log_activity(
                            "Local AI Analyst completed",
                            "AI"
                        )


# ============================================================
# FOOTER
# ============================================================

footer_html = textwrap.dedent("""
    <div style="margin-top:2.5rem;padding:24px 18px 20px;text-align:center;border:1px solid rgba(128,128,128,.22);border-radius:16px;background:linear-gradient(135deg,rgba(99,102,241,.07),rgba(14,165,233,.04));">
        <div style="font-size:1.35rem;font-weight:700;letter-spacing:.2px;margin-bottom:6px;">🤖 Analytix AI</div>
        <div style="font-size:.95rem;opacity:.82;margin-bottom:14px;">Your Personal AI Data Analyst</div>
        <div style="display:inline-block;padding:6px 12px;border-radius:999px;background:rgba(128,128,128,.10);font-size:.78rem;">Python • Streamlit • Ollama</div>
        <div style="margin-top:15px;font-size:.82rem;opacity:.72;">Developed by <strong style="opacity:1;">RK</strong></div>
        <div style="margin-top:5px;font-size:.75rem;opacity:.58;">© 2026 Analytix AI</div>
    </div>
""").strip()
st.markdown(footer_html, unsafe_allow_html=True)
