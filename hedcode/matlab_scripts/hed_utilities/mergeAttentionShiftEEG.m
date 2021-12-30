key = 'sub-004';
file1 = 'G:\AttentionShift\AttentionShiftWorking1\sourcedata\sub-004\eeg\sub-004_task-AuditoryVisualShift_run-01_eeg.set'; 
file2 = 'G:\AttentionShift\AttentionShiftWorking1\sourcedata\sub-004\eeg\sub-004_task-AuditoryVisualShift_run-02_eeg.set';
file3 = 'G:\AttentionShift\AttentionShiftWorking1\sub-004\eeg\sub-004_task-AuditoryVisualShift_run-01_eeg.set';

% key = 'sub-036';
% file1 = 'G:\AttentionShift\AttentionShiftWorking1\sourcedata\sub-036\eeg\sub-036_task-AuditoryVisualShift_run-01_eeg.set'; 
% file2 = 'G:\AttentionShift\AttentionShiftWorking1\sourcedata\sub-036\eeg\sub-036_task-AuditoryVisualShift_run-02_eeg.set';
% file3 = 'G:\AttentionShift\AttentionShiftWorking1\sub-036\eeg\sub-036_task-AuditoryVisualShift_run-01_eeg.set';

EEG1 = pop_loadset(file1);
EEG2 = pop_loadset(file2);

srate1 = EEG1.srate;
srate2 = EEG2.srate;
if (srate1 ~= srate2)
    error('sampling rates incorrect cannot continue');
end

fprintf('[%s]: Copy EEG1 into EEG3\n', key)
EEG3 = EEG1;
EEG3.data = [EEG1.data, EEG2.data];
fprintf('[%s]: Concatenate EEG1.data and EEG2.data to be EEG3.data\n', key)
EEG3.pnts = EEG1.pnts + EEG2.pnts;
fprintf('[%s]: Add EEG1.pnts and EEG2.pnts to be EEG3.pnts\n', key)
EEG3.times = 1000*((1:EEG3.pnts) - 1)/EEG3.srate;
fprintf('[%s]: Updating the EEG3.times\n', key)
EEG3.xmax = (size(EEG3.data, 2) - 1)/EEG3.srate;
fprintf('[%s]: Updating the EEG3.xmax\n', key)
EEG3.comments = ['Merging file1 comments [' EEG1.comments '] and ' ...
                 'file2 comments [' EEG2.comments '] for EEG3'];
fprintf('[%s]: Merging the comments for EEG1 and EEG2 for EEG3.\n', key)

pnts1 = EEG1.pnts;
events1 = EEG1.event;
nevents1 = length(EEG1.event);
events2 = EEG2.event;
latency2 = cell2mat({events2.latency}) + pnts1;
for k = 1:length(events2)
    events2(k).latency = latency2(k);
    events2(k).sample_offset = latency2(k);
    events2(k).urevent = k + nevents1;
end
fprintf(['[%s]: Updated latency, sample_offset and urevent in EEG2 ' ...
        'events\n'], key);
events3 = [events1,  events2];
fprintf('[%s]: Concatenated the EEG1 and EEG2 events for EEG3\n', key);
EEG3.event = events3;
pop_saveset(EEG3, 'filename', file3, 'savemode', 'twofiles');
fprintf('[%s]: Save the EEG3 file as run-01\n', key);
fprintf('[%s]: Manually merge the run-01 and run-02 event.tsv files\n', key);