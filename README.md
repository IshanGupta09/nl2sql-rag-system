<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00d4ff,50:8b5cf6,100:f472b6&height=220&section=header&text=NL2SQL%20RAG%20System&fontSize=56&fontColor=ffffff&fontAlignY=40&desc=Ask%20in%20Plain%20English%20%C2%B7%20Get%20SQL%20%C2%B7%20Get%20Answers&descAlignY=60&descSize=20&animation=fadeIn" />

</div>

<div align="center">

[![Live Demo](https://img.shields.io/badge/🚀%20LIVE%20DEMO-nl2sql--rag.streamlit.app-00d4ff?style=for-the-badge)](https://nl2sql-rag.streamlit.app/)
[![Stars](https://img.shields.io/github/stars/IshanGupta09/nl2sql-rag-system?style=for-the-badge&color=8b5cf6&logo=github&logoColor=white)](https://github.com/IshanGupta09/nl2sql-rag-system/stargazers)
[![Forks](https://img.shields.io/github/forks/IshanGupta09/nl2sql-rag-system?style=for-the-badge&color=f472b6&logo=github&logoColor=white)](https://github.com/IshanGupta09/nl2sql-rag-system/network/members)
[![MIT License](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](LICENSE)

</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit_Cloud-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq_API-F55036?style=flat-square&logoColor=white)](https://groq.com)
[![Llama](https://img.shields.io/badge/Llama_3.3_70B-7C3AED?style=flat-square&logo=meta&logoColor=white)](https://groq.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![FAISS](https://img.shields.io/badge/FAISS_+_MiniLM-0078D4?style=flat-square&logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

</div>

<br/>

<div align="center">

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   "Which customer placed the most orders last month?"                   │
│                              ↓                                          │
│   SELECT name, COUNT(*) FROM customers JOIN orders ... LIMIT 1;         │
│                              ↓                                          │
│   "Alice placed the most orders with 12 orders last month."             │
│                                                                         │
│            ⚡ All in ~2 seconds  ·  100% benchmark accuracy             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

</div>

---

## 🎥 Demo

<div align="center">

<img src="https://raw.githubusercontent.com/IshanGupta09/nl2sql-rag-system/main/assets/demo.gif" width="100%" alt="NL2SQL Demo"/>

_Can't see the GIF? Watch live → **[nl2sql-rag.streamlit.app](https://nl2sql-rag.streamlit.app/)**_

</div>

---

## 🏆 Benchmark

<div align="center">

<table>
<tr>
<td align="center" width="33%">

### 📊 100%
**Benchmark Accuracy**
25 / 25 Questions

</td>
<td align="center" width="33%">

### ⚡ ~2s
**Average Query Time**
SQL + NL Answer

</td>
<td align="center" width="33%">

### 🗄️ 4
**Tables Tested**
200 orders · 50 customers

</td>
</tr>
</table>

| Category | Score | Status |
|:---|:---:|:---:|
| 🔵 &nbsp; Simple SELECT | 5 / 5 | ✅ |
| 🟣 &nbsp; Filter (WHERE) | 5 / 5 | ✅ |
| 🟠 &nbsp; Aggregation (SUM · AVG · COUNT) | 5 / 5 | ✅ |
| 🔴 &nbsp; JOIN (multi-table) | 5 / 5 | ✅ |
| 🟡 &nbsp; Date Filter | 5 / 5 | ✅ |
| **⚡ &nbsp; Overall** | **25 / 25** | **🏆 100%** |

</div>

---

## ✨ Features

<div align="center">

<table>
<tr>
<td width="50%" valign="top">

### 🧠 Intelligence
- **NL → SQL** — plain English to precise SQL
- **NL Answers** — results in one clear sentence
- **RAG Pipeline** — FAISS + MiniLM context injection
- **Auto Correction** — SQL errors trigger retry

</td>
<td width="50%" valign="top">

### 🗄️ Database
- **Multi-Database** — upload any SQLite `.db` file
- **Schema Discovery** — auto-detected, no config
- **ecommerce.db** — demo database included
- **CSV Export** — download any result table

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🎨 Interface
- **Cyberpunk UI** — animated dot-grid + scanline
- **Session Counter** — 8 query limit with live bar
- **Query History** — recent queries in sidebar
- **Feedback** — 👍 / 👎 rating per answer

</td>
<td width="50%" valign="top">

### 🔒 Production
- **SQL Safety** — blocks all destructive ops
- **Streamlit Secrets** — API key never in code
- **Cloud Ready** — Streamlit Cloud deployment
- **Error Recovery** — graceful fallback answers

</td>
</tr>
</table>

</div>

---

## 🔄 Architecture

<div align="center">

<img src="https://raw.githubusercontent.com/IshanGupta09/nl2sql-rag-system/main/assets/architecture.svg" width="100%" alt="NL2SQL Architecture"/>

</div>

---

## 🛠️ Tech Stack

<div align="center">

<table>
<tr><th>Layer</th><th>Technology</th><th>Purpose</th></tr>
<tr>
  <td>🎨 <b>Frontend</b></td>
  <td><img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white"/></td>
  <td>Animated cyberpunk UI</td>
</tr>
<tr>
  <td>🤖 <b>LLM</b></td>
  <td><img src="https://img.shields.io/badge/Groq_Llama_3.3_70B-F55036?style=flat-square"/></td>
  <td>SQL generation + NL answers</td>
</tr>
<tr>
  <td>🔍 <b>RAG</b></td>
  <td><img src="https://img.shields.io/badge/FAISS_+_MiniLM-0078D4?style=flat-square"/></td>
  <td>Business context retrieval</td>
</tr>
<tr>
  <td>🗄️ <b>Database</b></td>
  <td><img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white"/></td>
  <td>Query execution</td>
</tr>
<tr>
  <td>⚙️ <b>API</b></td>
  <td><img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/></td>
  <td>REST backend (local/Docker)</td>
</tr>
<tr>
  <td>☁️ <b>Deploy</b></td>
  <td><img src="https://img.shields.io/badge/Streamlit_Cloud-FF4B4B?style=flat-square&logo=streamlit&logoColor=white"/></td>
  <td>Live hosting</td>
</tr>
</table>

</div>

---

## 📁 Project Structure

```
nl2sql-rag-system/
│
├── 🚀 streamlit.py              # Main app — standalone, Cloud ready
├── ⚙️  api.py                   # FastAPI backend (local/Docker only)
├── 📋 requirements.txt
├── 🔒 .gitignore
│
├── .streamlit/
│   └── config.toml              # Dark theme config
│
├── assets/
│   └── demo.gif                 # Demo recording
│
├── data/
│   ├── ecommerce.db             # Demo SQLite database
│   └── .gitkeep
│
├── docs/
│   └── business_rules.txt       # Domain context for RAG
│
├── llm/
│   └── sql_generator.py         # Groq — SQL generation + correction
│
├── nlg/
│   └── answer_generator.py      # Groq — rows → plain English
│
├── rag/
│   ├── ingest.py                # Build FAISS vectorstore
│   └── retriever.py             # Retrieve context per question
│
└── eval/
    ├── benchmark.py             # 25-question benchmark
    ├── questions.json           # Test questions
    └── report.py                # Benchmark report
```

---

## 💡 Example Queries

<div align="center">

| 💬 You Ask | 🤖 AI Answers |
|:---|:---|
| `What is the total revenue?` | *"The total revenue is $70,071.24."* |
| `Which customer placed the most orders?` | *"Alice placed the most orders with 12 orders."* |
| `List premium customers from the North` | Returns matching table |
| `How many orders last month?` | *"There were 18 orders placed last month."* |
| `Top 5 customers by total spend` | Returns ranked table |
| `Average order value?` | *"The average order value is $350.36."* |

</div>

---

## ☁️ Deploy on Streamlit Cloud

> Get your own live instance in under 5 minutes, **for free**.

**1 — Fork this repo**

[![Fork](https://img.shields.io/badge/🍴_Fork_This_Repo-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/IshanGupta09/nl2sql-rag-system/fork)

**2 — Go to [share.streamlit.io](https://share.streamlit.io)**
- Create app → select your fork → main file: `streamlit.py`

**3 — Add API key in Secrets**
```toml
GROQ_API_KEY = "gsk_your_key_here"
```
Free key at [console.groq.com](https://console.groq.com) — no credit card.

**4 — Deploy 🎉** · Live in ~2 minutes.

---

## 💻 Run Locally

```bash
# Clone
git clone https://github.com/IshanGupta09/nl2sql-rag-system.git
cd nl2sql-rag-system

# Setup
python -m venv venv && source venv/bin/activate   # Mac/Linux
python -m venv venv && venv\Scripts\activate       # Windows

pip install -r requirements.txt
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# First time only
python rag/ingest.py

# Run
streamlit run streamlit.py
```

---

## 🧪 Benchmark

```bash
python eval/report.py
```
```
  ✅  Simple SELECT     5/5
  ✅  Filter            5/5
  ✅  Aggregation       5/5
  ✅  JOIN              5/5
  ✅  Date Filter       5/5
  ───────────────────────────
  🏆  Overall    25/25  100%
  ⚡  Avg time       1.94s
```

---

## 🔒 Security

| 🛡️ | Protection | Details |
|:---:|:---|:---|
| 🚫 | SQL Injection | Blocks `DROP` `DELETE` `UPDATE` `INSERT` `ALTER` `TRUNCATE` |
| 📁 | Path Traversal | Only `data/` directory is accessible |
| 🔑 | API Key | Streamlit Secrets — never in code or GitHub |
| ⏱️ | Rate Limiting | Max 8 queries / session on live demo |
| 👁️ | Read-Only | All queries enforced as `SELECT` only |

---

## 🤝 Contributing

```bash
git checkout -b feature/your-feature
git commit -m "feat: your change"
git push origin feature/your-feature
# Open a Pull Request ↗
```

---

## 📄 License

MIT License — see [`LICENSE`](LICENSE) for details.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:f472b6,50:8b5cf6,100:00d4ff&height=140&section=footer&animation=fadeIn" />

### 👤 Ishan Gupta

[![GitHub](https://img.shields.io/badge/GitHub-IshanGupta09-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/IshanGupta09)
&nbsp;
[![LinkedIn](https://img.shields.io/badge/LinkedIn-ishan--gupta091-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ishan-gupta091/)

<br/>

**Found this useful? Give it a ⭐ — it helps a lot!**

<br/>

[![Star](https://img.shields.io/github/stars/IshanGupta09/nl2sql-rag-system?style=social)](https://github.com/IshanGupta09/nl2sql-rag-system)
&ensp;
[![Fork](https://img.shields.io/github/forks/IshanGupta09/nl2sql-rag-system?style=social)](https://github.com/IshanGupta09/nl2sql-rag-system/fork)

<br/>

*Built with ❤️ and ⚡ · Ishan Gupta · 2026*

</div>
