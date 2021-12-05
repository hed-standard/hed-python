## Summary of processing changes for Sternberg

Order of script execution:

| Script                              | Description  |
| ----------------------------------- | ------------ |
| [sternberg_preliminary_summary](#preliminary-summary-and-manual-editing)  | Summarize event file contents |
| [sternberg_preliminary_restructure](#preliminary-restructuring) | Add and remove columns and events. Convert as necessary and fill empty slots with 'n/a' |
| [sternberg_secondary_summary](#summarize-and-recheck-events) | Resummarize events and do additional checks. |
| [sternberg_remap](#remap-columns)   | Perform the orthogonal remapping of the columns and adjust specifics. |
| [sternberg_final_copy](#final-copy) | Copy to directory. |
| [sternberg_final_summary](#final-summary) | Perform final summary and recheck. |
| sternberg_final_extract(#final-extract) | Extract spreadsheet of values for HED tagging |

### Preliminary summary and manual editing


1. `sub-022_run-1` and `sub-022_run-2` each had an event at the end of the
file with value `empty`. These have been removed manually in `_events.tsv` and
`_events_temp.tsv`.
 2. The following had extra key press events at the beginning of the recording
which were removed:  `sub-003_run-3`(2), `sub-004_run-2`(5), `sub-004_run-4`(3),
`sub-006_run-1`(8), `sub-008_run-1`(4), `sub-009_run-4`(2), `sub-021_run-2`(2),
`sub-021_run-2`(2).
 3. `sub-015_run-3`(4) had extra key presses at the end of the file without a trial.
These were removed as well as a beginning boundary event.
 4. The EEG versions `sub-023_run-1`, `sub-023_run-2`, `sub-023_run-3`,
`sub-023_run-4`, and `sub-023_run-5` had the following extra 'n/a' columns: `event_code`, `cond_code`, and `sample_offset` which were removed.

### Preliminary restructuring

#### BIDS events restructuring

Create `events_temp2.tsv` files restructured as follows:
 1. Remove columns `response_time`, `trial_type`, and `stim_file`.
 2. Convert the `duration` column from samples to seconds so that it is compliant with BIDS.
 3. Convert the `value` column to have all string values.
 4. Replace `value` column empty slots and slots with `empty` with `n/a`.
 5. Remove `boundary` events from beginning of files.
 6. Add which has columns `event_type`, `task_role`, `memory_cond`, `trial` and
`letter`  filled with 'n/a'.

#### EEG.event restructuring

Create `_events_temp3.tsv` files restructured as follows:
 1. Remove columns `TTime`, `Uncertainy`, `Uncetainty2`, `ReqTime`, `ReqDur`,
`init_index`, `init_time`, and `urevent`.
 2. Convert the `duration` column from samples to seconds so that it is compliant with BIDS.
 3. Convert the `type` column to have all string values.
 4. The `type` column has some empty slots which are replaced with 'n/a'.
 5. Remove boundary events from beginning of files.

### Summarize and recheck events

This script resummarizes the data. The script also compare the values from

### Remap columns
Create `_events_temp4.tsv` from `_events_temp2.tsv` files as follows:
1. Run remapping of `value` to `event_type`, `task_role`, and `letter`.
2. Set the `trial` column based on the `ready` value in the `task_role`.
3. Count the number of targets in each trial and set the `memory_cond`.
4. Change the following `task_role` items based on contents:
  1. `in_correct` or `out_correct` to `continue` if last item in trial.
  2. `probe_target` to `probe_nontarget` for probes that are non targets.
  3. `probe_target` to `probe_out` for probes that are neither targets or non-targets.
  4. `in_group_correct` to `in_group_incorrect` to indicate left button but should have been right.
  5. `out_group_correct` to `out_group_incorrect` to indicate right button but should have left.
  6. `bad_trial` if number of events in the trial is not 14 or 13. (Also check that if 13,
it is the feedback event that is missing.

### Final copy

Copy all of the event files to an info directory for uploading.

### Final summary

The following trials do not have a feedback events:

| Subject | Run | Trials     | 
| ------- | --- | ---------- |
| 5       | 1-4 | all        | 
| 6       | 3   | 21         | 
| 7       | 1   | 3          | 
| 7       | 2   | 9,12,13,14 | 
| 7       | 3   | 9,16       | 
| 7       | 4   | 8,13       | 
| 22      | 1   | 22         |
| 22      | 2   | 14         | 

The following are **bad trials**.  They have no events except for the fixation presentation and
key clicks.

| Subject | Run | Trials     | 
| ------- | --- | ---------- |
| 6       | 1   | 2, 3       | 
| 14      | 1   | 11         | 
| 14      | 2   | 3,11       | 
| 14      | 3   | 22         | 
| 17      | 3   | 3,5        |
| 22      | 6   | 6          |

### Final extract

Extract a spreadsheet with unique event values in preparation for tagging. 