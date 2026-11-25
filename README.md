# Pandas Study Notebook

A structured notebook for learning and reviewing pandas through explanations, worked examples, and practice exercises. It builds on basic Python and NumPy knowledge and progresses toward data cleaning, analysis, and preparation for machine learning.

**The README is in English. The notebook explanations and exercises are in Turkish.**

[Open the notebook](Pandas_Detayli_Calisma.ipynb)

## Learning format

Each topic follows the same sequence:

1. Read the explanation, divided into focused headings.
2. Run a worked example and review how the result was produced.
3. Solve a similar exercise using the provided data.
4. Open a hint if needed, then compare your answer with the solution key.

The notebook contains **18 chapters, 36 worked examples, and 36 practice exercises**. Exercises have a short goal, a target output, and a starter cell. Hints and solutions are in collapsible sections; the solution key is at the end.

## Topics

| Chapters | Coverage |
| --- | --- |
| 01–03 | Series, DataFrame, inspecting tables, column selection, `loc` and `iloc` |
| 04–06 | Filtering, derived columns, safe updates, indexes, and label alignment |
| 07–09 | Missing values, data types, text cleaning, sorting, and duplicate records |
| 10–13 | Grouping, aggregation, mapping, `transform`, joins, and reshaping |
| 14–16 | Dates, time series, CSV input/output, and plotting |
| 17 | A small expense analysis combining cleaning, summaries, and budget comparisons |
| 18 | Optional ML preparation: training-only statistics and consistent categorical columns |

Chapters 01–16 form the core learning path. Chapter 17 combines those skills, while Chapter 18 can be revisited when starting machine learning.

## Getting started

Use Python 3.12 with VS Code's Jupyter extension, JupyterLab, or another compatible notebook editor.

Install the required packages in the Python environment you will use as the notebook kernel:

```bash
python -m pip install pandas numpy matplotlib ipykernel
```

If you use VS Code, open `Pandas_Detayli_Calisma.ipynb`, select that Python environment as the kernel, and run the setup cell first. Then work through the topics in order.

The notebook uses small, synthetic datasets defined in its cells. No external dataset download or separate CSV file is required. CSV examples use in-memory text buffers.

## Working on exercises

Replace `sonuc = None` in each exercise cell with your solution. Some tasks may need a few lines; assign the final result to `sonuc`. The existing display block will show your answer.

Each example and exercise creates its own input data after the shared imports. Empty starter cells can run without errors, but this does **not** mean the exercises have been completed or graded automatically.

## Validation

Worked examples, exercise solutions, and empty starter cells were checked separately. The notebook was also executed from start to finish using:

- Python 3.12
- pandas 3.1.1
- NumPy 2.5.5
- Matplotlib 3.11.2

The setup cell prints the versions in your selected environment.

Prepared with Codex support as part of an AI/ML learning path. Links to the official pandas documentation are included at the end of the notebook.
