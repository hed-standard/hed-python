## Processing summary for Attention Shift

The scripts assume that an `_events_temp.tsv` file has been extracted from the EEG.set files for each `_events.tsv` file.  

Order of script execution:


| Script                              | Description  |
| ----------------------------------- | ------------ |
| [as_preliminary_summary](#preliminary-summary-and-manual-editing)  | Summarize event file contents |



### Issues
 sub-004 of the attention shift data.  The subject has two runs.  The first run is really short.  The second run won't read correctly with EEGLAB and truncates the data.   Can you look at this?  We may have to delete this subject entirely.  Let me know.... Thanks, Kay

pop_loadset(): loading file G:\AttentionShift\AttentionShiftWorking\sub-004\eeg\sub-004_task-AuditoryVisualShift_run-02_eeg.set ...
Reading float file 'G:\AttentionShift\AttentionShiftWorking\sub-004\eeg\sub-004_task-AuditoryVisualShift_run-02_eeg.fdt'...
WARNING: The file size on disk does not correspond to the dataset, file has been truncated
eeg_checkset error: binary data file likely truncated, importing anyway...
eeg_checkset note: upper time limit (xmax) adjusted so (xmax-xmin)*srate+1 = number of frames
Creating a new ALLEEG dataset 1


Checking the validity of the event codes:
sub-005_run-01 has 5 shift event codes in a focus condition
sub-008_run-01 has 2874 shift event codes in a focus condition
sub-015_run-01 has 239 focus event codes in a shift condition
sub-036_run-01 has 721 focus event codes in a shift condition  (Run-02 seems to be the better run?)

Codes 1 and 2 can appear anywhere.
Codes 3 through 6 should appear only in the focus condition.
Codes 7 through 14 should appear only in the shift condition.
Codes 199, 201, 202, and 255 are not related to condition.
