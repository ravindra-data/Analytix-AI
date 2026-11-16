# 🤖 Analytix AI

### AI-Powered Personal Data Analyst

Analytix AI is an intelligent data analytics application built using Python, Streamlit, and AI models. It helps users analyze datasets, clean data, visualize patterns, generate insights, and interact with their data using natural language.

The application supports **Groq AI for cloud-based intelligence** and **Ollama for local AI processing**.

---

## 🚀 Features

- 📊 **Automated Data Analysis** – Analyze datasets and generate statistical summaries.
- 🧹 **Data Cleaning** – Identify and handle missing values and duplicate records.
- 📈 **Data Visualization** – Generate charts and visualizations.
- 🤖 **AI-Powered Insights** – Get intelligent explanations and recommendations.
- 🧠 **Autonomous Analysis** – Automatically analyze datasets and generate reports.
- 💬 **Ask Your Data** – Interact with datasets using natural language.
- 🖥️ **Local AI Analyst** – Run AI analysis locally using Ollama.
- ☁️ **Cloud AI Integration** – Use Groq API for cloud-based AI responses.
- 📁 **Workspace Management** – Manage datasets and analysis workflows.
- 📜 **Analysis History** – Access previous analysis activities.
- 📑 **Report Generation** – Generate downloadable analytical reports.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| Pandas | Data manipulation and analysis |
| NumPy | Numerical computing |
| Matplotlib | Data visualization |
| Seaborn | Statistical visualization |
| Ollama | Local AI inference |
| Groq API | Cloud AI inference |
| Git & GitHub | Version control |

---

## 🧠 AI Integration

Analytix AI supports two AI providers:

### ☁️ Groq AI
- Cloud-based AI processing.
- Fast AI-generated insights and recommendations.
- Configured using `GROQ_API_KEY`.
- Suitable for Streamlit Cloud deployment.

### 🖥️ Ollama
- Local AI processing.
- Runs AI models on your own machine.
- Uses `llama3.2:3b` by default.
- Does not require a cloud API key for local inference.

---

## 📂 Supported Data Formats

- CSV
- Excel (`.xlsx`, `.xls`)

---

## ⚙️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/ravindra-data/Analytix-AI.git
cd Analytix-AI
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

Download Ollama:

https://ollama.com/download

Pull the required model:

```bash
ollama pull llama3.2:3b
```

Start Ollama:

```bash
ollama serve
```

### 5. Run Application

```bash
streamlit run app.py
```

---

## 🔑 Groq API Configuration

For cloud AI functionality, configure the following environment variable:

```bash
GROQ_API_KEY=your_groq_api_key
```

For Streamlit Cloud deployment, add the API key under:

**App Settings → Secrets**

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Never commit your actual API key to GitHub.

---

## 🌐 Live Application

**GitHub Repository:**  
https://github.com/ravindra-data/Analytix-AI

**Live Demo:**  
[Analytix AI – Streamlit Cloud](https://analytix-ai.streamlit.app/)

---

## 👨‍💻 Developer

**Ravindra Kumar**

GitHub: [@ravindra-data](https://github.com/ravindra-data)

---

## ⭐ Project Highlights

- AI-powered data analytics.
- Automated analytical workflows.
- Cloud and local AI integration.
- Interactive Streamlit interface.
- Practical application of Python and AI technologies.

---

### Built with Python, Streamlit, Groq AI & Ollama ❤️