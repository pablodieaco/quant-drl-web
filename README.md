# 📊 quant-drl-web

**quant-drl-web** is a Streamlit-based interactive dashboard for visualizing, evaluating, and simulating Deep Reinforcement Learning (DRL) models applied to portfolio management.

It serves as the frontend for the [`quant-drl-core`](https://github.com/pablodieaco/quant-drl-core) research framework, providing a user-friendly interface for financial data exploration, model comparison, and portfolio decision analysis.

> 🎓 Developed as part of my **Final Degree Project (TFG)** in the **Double Degree in Mathematics and Computer Engineering** at the **University of Seville**.

---

## ✨ Features

- 📈 **Model evaluation & metrics explorer**
- 💡 **Portfolio simulation and strategy testing**
- 🧠 **Deep RL integration** (PPO, SAC)
- 🔌 **Database-backed** via PostgreSQL
- 🎨 **Streamlit** multipage navigation
- 🐳 Docker & Docker Compose for deployment
- 📂 Examples and demo models included

---

## 🖼️ Preview
TODO
<!-- 🖼️ You can replace this with a GIF or a screenshot

<!-- ![App Preview](assets/dashboard_preview.gif) -->

<!-- > _Insert a short demo GIF or screenshot of the Streamlit app here_
> - You can use `peek` or `screen-to-gif` to record your screen
> - Save it to `/assets/` and link it above --> -->

---

## 📁 Project Structure

```bash
quant-drl-web/
├── web/                # Streamlit app (modular)
│   ├── app.py          # Main entry point
│   ├── pages/          # UI Pages (Streamlit multipage)
│   ├── commons/        # Session & layout
│   └── db/             # DB scripts and seeders
├── examples/           # Sample models and evaluation results
│   ├── models/         # Pretrained DRL models
│   └── results/        # evaluation_results.csv
├── docker-compose.yml  # Launch web + PostgreSQL
├── Dockerfile          # Web app container
├── build.sh            # Script to copy core + build
└── requirements.txt    # Python dependencies
```

---

## ⚙️ Requirements

- Docker & Docker Compose
- Python 3.10+ (optional for local runs)
- `quant-drl-core` available locally (used during build) (TODO: It will not be necessary in future releases)

---

## 🚀 Quickstart

### 1. Clone the repo 
```bash
git clone https://github.com/pablodieaco/quant-drl-web.git
cd quant-drl-web
```

### 2. Build with local quant-drl-core

```bash
./build.sh
```
This script will:

- Copy your local quant-drl-core/ into a temporary folder

- Exclude unnecessary files (e.g., .venv/, logs/, notebooks/)

- Build the Docker image and install the core as an editable package

### 3. Launch the app

```bash
docker-compose up
```
Once running, the app will be available at http://localhost:8501

### 4. Alternative: Build and Launch

```bash
./build.sh yes
```

---

## 🧪 Example Models

We’ve included pretrained models and example evaluation results inside the `examples/` folder:
- `examples/models/` → PPO and SAC agents
- `examples/results/evaluation_results.csv`→ model evaluation scores

---

## 🧠 About this project

This dashboard is part of a broader research framework:

👉 Check out `quant-drl-core` for:
- DRL training pipelines (PPO, SAC)
- Custom Gym environments
- Evaluation and visualization logic
- Experiment reproducibility



## 📝 License

This project is licensed under the **MIT License**.  
See the [LICENSE](./LICENSE) file for details.

---

## 🙋‍♂️ Author

Made with ❤️ by **Pablo Diego Acosta**

- 💼 LinkedIn: [linkedin.com/in/pablodiegoacosta](https://www.linkedin.com/in/pablodiegoacosta)

---

## ✨ Todo / Ideas

- [ ] Embed live charts from financial APIs
- [ ] Auto-refresh evaluation dashboard with scheduled updates
- [ ] Live inference from trained DRL models