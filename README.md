# NuggetsManagement ♟️⛏️

**NuggetsManagement** is a high-performance software for the automated extraction, analysis, and classification (qualimetry) of "chess nuggets" from massive game databases in PGN format.

The project was created to support academic research on computer chess (awarded international recognition) and aims to provide datasets of critical positions for human training, correspondence chess, and stress-testing NNUE-based UCI engines.

## 📖 The Concept of a "Nugget"
A **nugget** is defined as a chess position characterized by a high degree of tension and dynamic complexity. Rather than relying on the traditional Centipawn (CP) evaluation, the software filters positions using the probabilistic **Win/Draw/Loss (WDL)** model.
A position is considered a nugget if the win probability (WDL Expectation) for one side falls on specific critical targets (e.g., 75% or 25%), with a configurable tolerance margin.

## ✨ Key Features
* **Asynchronous Processing:** Uses `asyncio` to launch multiple UCI engine instances in parallel, maximizing CPU usage and cutting down I/O time.
* **Native WDL Filter:** Queries modern engines (such as Stockfish 16+) leveraging the `UCI_ShowWDL` option.
* **Advanced Qualimetry:** Computes complex metrics at $O(1)$ computational cost thanks to the use of Bitboards:
  * *Game Phase* (Smirnov's algorithm, based on material and half-move count).
  * *Center Type* (Open, Closed, Static, Mobile, Dynamic, with IQP and hanging pawns analysis).
  * *Tactical Tension* (count of instantaneous legal captures).
  * *Material Asymmetry*.
* **Historical Qualimetry:** Automatically tracks *Frequency* (how many times the nugget appears in the database) and *Recency* (the most recent date it was played), skipping redundant analyses thanks to a thread-safe in-RAM cache.
* **Structured Output:** Exports results in formats ready for data analysis (`.jsonl`, `.csv`).

## 🛠️ Prerequisites
* **UCI Engine:** A Stockfish executable (version 16 or higher) with NNUE support.
* For development from source code: **Python 3.9+**.

## 🚀 Installation (Development)
If you want to run the software from source code or modify it:

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR-USERNAME/NuggetsManagement.git](https://github.com/YOUR-USERNAME/NuggetsManagement.git)
   cd NuggetsManagement
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Running the Program (Source)
Once you've set the parameters in the `config.json` file and activated the virtual environment, make sure you're in the project's root directory and run the following command from the terminal:

```bash
python src/main.py
```

## ⚙️ Configuration (`config.json`)
The software's behavior is entirely managed through the `config.json` file located in the project root. Before starting the analysis, make sure to fill in these parameters:

* `engine_path`: The absolute or relative path to the UCI engine executable (e.g., `"C:\\paths\\stockfish.exe"` on Windows, or `"stockfish"` on Linux if it's in the PATH).
* `pgn_path`: The path to the PGN file containing the games database to analyze (e.g., `"data/games.pgn"`).
* `output_dir`: The folder where the final reports (JSONL, CSV, HTML) will be saved.
* `concurrency`: The number of engine processes to launch in parallel. Set it based on your CPU's physical cores (e.g., `4` or `8`).
* `analysis_time`: The time in seconds dedicated to WDL (and MultiPV) analysis for each individual position (e.g., `1.0`).
* `wdl_tolerance`: The tolerance margin relative to the WDL targets (75% and 25%). For example, `0.06` means a tolerance of $\pm$ 6% (it will capture values between 69% and 81%).
* `threads`: The number of CPU threads allocated per *single* engine instance (e.g., `1`). Note: the total number of threads used will be `concurrency * threads`.
* `hash`: The size of the Hash Table (in MB) allocated per instance (e.g., `64`).
* `syzygy_path`: (Optional) The path to the endgame tablebases (e.g., `"C:\\syzygy"`). Leave empty `""` if not used.

## 📦 Generating the Executable (Standalone)

You can compile NuggetsManagement into a single executable file to distribute it without requiring the end user to install Python or set up a virtual environment. We use `pyinstaller`.

**⚠️ Important note:** Compilation is not cross-platform. To generate a `.exe` for Windows, you must run the command on Windows. To generate a Linux binary, you must run it on Linux.

### 1. Preparation
Make sure your virtual environment (`.venv`) is activated, since PyInstaller needs to "see" the installed libraries (such as `python-chess`).
```bash
pip install pyinstaller
```

### 2. Compilation
Run the command corresponding to your operating system from the project's root folder:

**On Windows:**
```bash
pyinstaller --onefile --name NuggetsManagement src/main.py
```
**On Linux:**
```bash
pyinstaller --onefile --name NuggetsManagement_linux src/main.py
```
(On Linux, remember to grant execution permissions to the generated file with chmod +x dist/NuggetsManagement_linux.)

### 3. How to Distribute the Software
PyInstaller packages the Python code but does not include external files, by architectural choice (we want the user to be able to change settings without recompiling).

To distribute the program, create a folder and place the following files in it, taking the executable you just built from the dist/ folder:

```text
NuggetsManagement_Release/
│
├── NuggetsManagement.exe    <-- The compiled file (from dist/)
├── config.json              <-- The configuration file
├── stockfish.exe            <-- The chess engine
└── data/                    <-- The folder with the PGNs to analyze
    └── games.pgn
```

The end user will simply need to open config.json, make sure the paths are correct, and double-click the executable!

## 📄 License
This project is distributed under the **MIT** license. Feel free to use, modify, and integrate it into your projects (commercial and non-commercial). See the `LICENSE` file for details.

## 🎓 Academic References
The theoretical concept underlying WDL extraction and nugget qualimetry won first prize at an international Artificial Intelligence conference in Japan.
Paper link: [Springer - 10.1007/978-3-032-02555-5_1](https://link.springer.com/chapter/10.1007/978-3-032-02555-5_1)
