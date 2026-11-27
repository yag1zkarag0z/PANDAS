# CSV Analyzer

A local Streamlit application for inspecting, cleaning, filtering, and summarizing CSV data with pandas. The interface and learning comments are in Turkish.

## Features

- CSV/TSV upload with delimiter and encoding controls.
- A sample expense file with duplicate records, invalid values, and extra whitespace.
- Original and working-table quality reports.
- Explicit number/date conversion, text trimming, duplicate removal, and missing-value handling.
- Numeric, date, or text filtering; sorting; column selection.
- Group summaries, bar charts, scatter plots, and correlation.
- Download the filtered working table or grouped summary as UTF-8 CSV.
- Restore the original table at any time.

Every cleaning run starts from a copy of the original data. Columns are initially read as text to preserve identifiers such as `001`; select the numeric and date columns explicitly. Median filling is an assumption, not a reconstruction of the original measurement.

## Run

On Windows, double-click `Baslat.bat`. It uses the project environment or the existing parent environment, installs the specified dependencies if needed, and starts Streamlit from the correct directory.

For manual setup, use Python 3.12. From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true
```

If the existing environment is in the parent `PANDAS` directory, run from **this project directory**:

```powershell
..\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true
```

Open the terminal's Local URL. Toggle **Örnek veriyi kullan**, review the preset rules, and press **Temizliği uygula**. The sample should produce 3 rows, a total expense of 200, and category totals of 160 for Yemek and 40 for Ulaşım.

## Streamlit Community Cloud

To deploy this app from the `yag1zkarag0z/PANDAS` repository, select:

- Branch: `main`
- Main file path: `csv-analyzer/app.py`
- Python version: `3.12`

The dependency file is next to the app at `csv-analyzer/requirements.txt`. The repository-root `.streamlit/config.toml` supplies the shared theme and upload settings. The nested configuration supports running this project directly as well.

## Read the code

1. `islemler.py`: CSV reading, cleaning, filtering, quality reports, grouped summaries, and CSV export.
2. `app.py`: Streamlit widgets, session state, and displaying the results.
3. `stil.css`: visual styling.

For a first code review, start with `csv_oku`, then follow `veriyi_temizle`. Test the behavior on the sample before changing a function.

The app accepts up to 10 MB, 100,000 rows, and 150 columns. Previews show up to 1,000 rows, while downloads include the full filtered result. Bar charts show the top 20 groups; scatter plots show a reproducible sample of up to 5,000 points. Files are processed in the application server's memory without a database or external AI service.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Built with Codex support for guided pandas practice.
