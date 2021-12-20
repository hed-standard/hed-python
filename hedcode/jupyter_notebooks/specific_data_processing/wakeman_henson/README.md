## Summary of processing changes for Wakeman-Henson

Order of script execution:

| Script                              | Output | Description  |
| ----------------------------------- | ------ | ------------ |
| [wh_1_fix_initial_events.ipynb](wh_1_fix_initial_events.ipynb)  | `_temp1` | Fix setup and initial face events. |
| [wh_2_restructure.ipynb](wh_2_restructure.ipynb) | `_temp2` | Add and remove columns and events. |
| [wh_3_check.ipynb](wh_3_check.ipynb) | | Summarize events and do additional checks. |
| [wh_4_cleanup.ipynb](wh_4_cleanup.ipynb) | | Remove and rename files on a copy of dataset. |
