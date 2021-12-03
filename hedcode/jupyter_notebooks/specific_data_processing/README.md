## Process for restructuring event files

The Jupyter notebooks in this directory illustrate how to check the consistency
and restructure event files to prepare for HED tagging.  Often this is an
iterative process.

The general steps are described in the following table:

**Table 1:** Sample template created from a BIDS dataset.

|Script                    | Purpose                            | 
| ------------------------ | ---------------------------------- | 
| `_preliminary_summary`     | Outputs column names and summarizes file contents |  
| `_preliminary_restructure` | Removes specified columns and rows. Converts categorical columns to strings and puts 'n/a' in empty columns. |

| 41    | 1          | n/a        | n/a       | n/a        |
| 42    | 2          | n/a        | n/a       | n/a        |
| 201   | 3          | n/a        | n/a       | n/a        |
