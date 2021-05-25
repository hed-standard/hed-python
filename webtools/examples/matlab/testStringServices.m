%% Shows how to call hed-services to obtain a list of services
host = 'http://127.0.0.1:5000';
%host = 'https://hedtools.ucsd.edu/hed';
csrf_url = [host '/services']; 
services_url = [host '/services_submit'];

% hedStrings = {['Event/Category/Experimental stimulus, ' ...
%                'Event/Label/Stimulus, Event/Description/Square display,'... 
%                'Sensory presentation/Visual, Invalid/Tag'], ...
%                ['Event/Category/Experimental stimulus, ' ...
%                 'Event/Label/Stimulus, Event/Description/Square display, ' ...
%                 'Sensory presentation/Visual'], ...
%                 ['Another bad tag']};
hedStrings = {['Red,Blue'], ['Green'], ['White,Black']}; 
%hedStrings = {['Red,Blue'], ['Blech'], ['Green']};
%% Send an empty request to get the CSRF TOKEN and the session cookie
[cookie, csrftoken] = getSessionInfo(csrf_url);

%% Set the header and weboptions
header = ["Content-Type" "application/json"; ...
          "Accept" "application/json"; ...
          "X-CSRFToken" csrftoken; ...
          "Cookie" cookie];

options = weboptions('MediaType', 'application/json', 'Timeout', 120, ...
                     'HeaderFields', header);
data = struct();
%data.service = 'string_validate';
data.service = 'string_to_long';
%data.schema_version = '7.1.2';
data.schema_version = '8.0.0-alpha.1';
data.string_list = hedStrings;
%data.check_for_warnings = false;
data.check_for_warnings = true;

%% Send the request and get the response for version 7.1.2
response = webwrite(services_url, data, options);
response = jsondecode(response);
fprintf('Error report:  [%s] %s\n', response.error_type, response.error_msg);

%% Print out the results if available
if isfield(response, 'results') && ~isempty(response.results)
    results = response.results;
    fprintf('[%s] status %s: %s\n', response.service, results.msg_category, results.msg);
    fprintf('HED version: %s\n', results.schema_version);
    fprintf('\nReturn data for service %s [%s]:\n', ...
        response.service, results.command);
    data = results.data;
    for k = 1:length(data)
        if ~isempty(data{k})
            fprintf('%s\n', data{k});
        else
            fprintf('HED string %d has no results\n', k);
        end
    end
end

