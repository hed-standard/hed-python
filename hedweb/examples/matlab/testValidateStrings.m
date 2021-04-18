%% Shows how to call hed-services to obtain a list of services
host = 'http://127.0.0.1:5000';
csrf_url = [host '/hed-services']; 
services_url = [host '/hed-services-submit'];

hedStrings = {['Event/Category/Experimental stimulus, ' ...
               'Event/Label/Stimulus, Event/Description/Square display,'... 
               'Sensory presentation/Visual, Invalid/Tag'], ...
               ['Event/Category/Experimental stimulus, ' ...
                'Event/Label/Stimulus, Event/Description/Square display, ' ...
                'Sensory presentation/Visual']};
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
data.service = 'validate_strings';
data.hed_version = '7.1.2';
%data.hed_version = '8.0.0-alpha.1';
data.check_for_warnings = true;
data.hed_strings = hedStrings;

%% Send the request and get the response for version 7.1.2
response = webwrite(services_url, data, options);
response = jsondecode(response);
validation_errors = response.result.validation_errors;
error_type = response.error_type;
message = response.message;
fprintf('Validation results for %d HED strings...\n\n', length(validation_errors))
for k = 1:length(validation_errors)
    if ~isempty(validation_errors{k})
        fprintf('%s\n', validation_errors{k});
    else
        fprintf('HED string %d has no errors\n', k);
    end
end
fprintf('\nError report: [%s] %s\n', error_type, message)
