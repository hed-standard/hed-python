%% Shows how to call hed-services to obtain a list of services
host = 'http://127.0.0.1:5000';
csrf_url = [host '/hed-services']; 
services_url = [host '/hed-services-submit'];
dictionary_file = '../data/good_dictionary.json';
json_text = fileread(dictionary_file);

%% Send an empty request to get the CSRF TOKEN and the session cookie
[cookie, csrftoken] = getSessionInfo(csrf_url);

%% Set the header and weboptions
header = ["Content-Type" "application/json"; ...
          "Accept" "application/json"; ...
          "X-CSRFToken" csrftoken; ...
          "Cookie" cookie];

options = weboptions('MediaType', 'application/json', 'Timeout', Inf, ...
                     'HeaderFields', header);
data = struct();
data.service = 'validate_json';
data.hed_version = '7.1.2';
%data.hed_version = '8.0.0-alpha.1';
data.check_for_warnings = true;
data.json_dictionary = string(json_text);

%% Send the request and get the response for version 7.1.2
response = webwrite(services_url, data, options);
response = jsondecode(response);
validation_errors = response.result.validation_errors;

if isfield(response, 'error_type')
    error_type = response.error_type;
else
    error_type = '';
end
if isfield(response, 'message')
    message = response.message;
else
    message = '';
end

fprintf('Validation results for %s\n', dictionary_file)
fprintf('%s\n', validation_errors)
fprintf('Error report: [%s] %s\n', error_type, message)
