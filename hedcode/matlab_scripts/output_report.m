function [] = output_report(response, theTitle)

fprintf('\nHED services report for %s\n', theTitle);
fprintf('Error report:  [%s] %s\n', response.error_type, response.error_msg);

%% Print out the results if available
if isfield(response, 'results') && ~isempty(response.results)
    results = response.results;
    fprintf('[%s] status %s: %s\n', response.service, results.msg_category, results.msg);
    fprintf('HED version: %s\n', results.schema_version);
    fprintf('\nReturn data for service %s [command: %s]:\n', ...
        response.service, results.command);
    data = results.data;
    if ~iscell(data)
        fprintf('%s\n', data);
    else
        for k = 1:length(data)
            if ~isempty(data{k})
                fprintf('[%d]: %s\n', k, data{k});
            end
        end
    end

    %% Output the spreadsheet if available
    if  isfield(results, 'spreadsheet')
        fprintf('\n----Spreadsheet result----\n');
        fprintf(results.spreadsheet);
    end
end