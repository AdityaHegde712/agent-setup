---
name: jupytext-notebooks
description: Instructions for safely reading, editing, and creating Jupyter Notebook (.ipynb) files. Explains how to use Jupytext to convert notebooks to python files, how to format them, and how to sync changes back.
---

# Jupyter Notebooks (Jupytext) Skill

When working with `.ipynb` files, **DO NOT** try to directly edit or generate the raw JSON structure. The JSON format is complex, requires strict escaping, and is prone to errors when modified manually.

Instead, always use **Jupytext** to convert the notebook into a plain Python script (using the `percent` format), make your edits there, and then sync those changes back to the `.ipynb` file.

## Required Operations

### 1. Converting a Notebook to a Python Script

To read or edit an existing Jupyter Notebook, first convert it to a python script using the `percent` format. This format separates notebook cells using special `# %%` comments.

Run the following command in the terminal:

```bash
jupytext --to py:percent notebook.ipynb
```

_(This command creates a file named `notebook.py` alongside the notebook)._

### 2. Formatting the Python Script

When editing or creating the `notebook.py` file, you must strictly follow the `percent` format so Jupytext knows how to translate it back into notebook cells.

- **Code Cells:** Start every new code cell with the exact string `# %%`.
- **Markdown Cells:** Start markdown cells with `# %% [markdown]`. Every subsequent line of the markdown cell must be a Python comment (i.e., it must start with `# `).

**Example of a properly formatted `notebook.py` file:**

```python
# %% [markdown]
# # Data Analysis
# This is a markdown cell describing the analysis.
# Notice how every line of markdown starts with a hash.

# %%
import pandas as pd
import numpy as np

# %% [markdown]
# ## Load Data
# We load the dataset below.

# %%
df = pd.read_csv('data.csv')
print(df.head())
```

### 3. Syncing Edits Back to the Notebook

After you have finished making edits to the `notebook.py` file, you must sync your changes back to the `.ipynb` file so the user can open it in Jupyter.

**To update an existing notebook and preserve its cell outputs**, use the `--update` flag:

```bash
jupytext --update --to notebook notebook.py
```

**If you are creating a completely new notebook** (or want to overwrite it without preserving outputs), use:

```bash
jupytext --to ipynb notebook.py
```

### 4. Executing Notebooks (Optional)

If the user asks you to execute the notebook after creating it, you can run the notebook headlessly using `nbconvert`:

```bash
# Execute the notebook and save the outputs back into the same file
jupyter nbconvert --to notebook --execute --inplace notebook.ipynb
```

## Summary Workflow

1. Run `jupytext --to py:percent <file>.ipynb`
2. Open `<file>.py` and edit it using the `# %%` format guidelines.
3. Run `jupytext --update --to notebook <file>.py` to save the changes.
