# 🎥 YouTube Summarizer

An AI-powered YouTube video summarizer that extracts transcripts from YouTube videos and generates concise summaries using OpenAI.

---

## 🚀 Features

* 🔗 Paste any YouTube video URL
* 📝 Automatically fetch video transcripts
* 🤖 Generate AI-powered summaries
* ⚡ Fast and lightweight
* 🌐 Simple web interface
* 📄 Clean and readable output

---

## 🛠️ Tech Stack

* **Python**
* **FastAPI**
* **OpenAI API**
* **YouTube Transcript API**
* **HTML / CSS / JavaScript**

---

## 📂 Project Structure

```bash
YT SUMMARISER/
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
├── static/
├── templates/
└── ...
```

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Bhvya11singh/YOUTUBE-SUMMARIZER.git
cd YOUTUBE-SUMMARIZER
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv .venv
```

Activate virtual environment:

#### Windows

```bash
.venv\Scripts\activate
```

#### Mac/Linux

```bash
source .venv/bin/activate
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Add OpenAI API key

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_api_key_here
```

---

## ▶️ Running the Project

Start the server:

```bash
uvicorn main:app --reload
```

or

```bash
python main.py
```

Open in browser:

```bash
http://127.0.0.1:8000
```

---

## 📌 How It Works

1. User enters a YouTube URL
2. Transcript is fetched using YouTube Transcript API
3. Transcript is processed and cleaned
4. OpenAI generates a concise summary
5. Summary is displayed on the webpage

---

## 🔒 Environment Variables

| Variable       | Description         |
| -------------- | ------------------- |
| OPENAI_API_KEY | Your OpenAI API key |

---

## 📷 Demo

Add screenshots or demo GIFs here.

---

## 🚧 Future Improvements

* Multi-language summaries
* Download summaries as PDF
* Video chapter generation
* AI notes & flashcards
* Dark mode UI
* User authentication

---

## 🤝 Contributing

Contributions are welcome!

Fork the repository and submit a pull request.

---

## 📜 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Bhavya Singh**

* GitHub: https://github.com/Bhvya11singh
* Email: [bhavyasssiii@gmail.com](mailto:bhavyasssiii@gmail.com)
