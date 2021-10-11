## Jupyter notebooks to demo HED tag processes

These notebooks demonstrate the process of redesigning event files and
adding HED tags. The goal of the redesign is to have orthogonal column
information that is clear and facilitates analysis. 

The demo scripts use data in `../data/sternberg` and in the reduced
attention shift dataset: 

[https://github.com/hed-standard/hed-examples/data/eeg_ds0028932](https://github.com/hed-standard/hed-examples/data/eeg_ds0028932).

The notebooks are designed to be executed in the following order:  

1. `summarize_events.ipynb` gather all of the unique values in the columns of
all of the events files in a BIDS dataset.  

2. `create_template.ipynb`  gathers all of the unique combinations of values in
a specified group of columns (the key columns) and creates a template file
for you to specify the mapping between each unique key and values in target columns.
This is the **event design** that must be filled in by the user.  

3. `remap_events.ipynb` creates new event files using the template from the previous
step to remap columns.

4. `tag_columns.ipynb` demonstrates how to create a list of the unique
values in the specified columns in a flattened form so that they can be tagged.