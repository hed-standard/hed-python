%% Shows how to call hed-services to obtain a list of services
%host = 'http://127.0.0.1:5000';
host = 'https://hedtools.ucsd.edu/hed';
csrf_url = [host '/services']; 
services_url = [host '/services_submit'];
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
data.service = 'dictionary_validate';
%data.service = 'dictionary_to_long';
%data.service = 'dictionary_to_short';
%data.schema_version = '7.1.2';
data.schema_version = '8.0.0-alpha.1';
data.json_string = string(json_text);
data.display_name = 'my JSON dictionary';
data.check_for_warnings = false;
%data.check_for_warnings = true;

%% Send the request and get the response 
response = webwrite(services_url, data, options);
response = jsondecode(response);
fprintf('Error report:  [%s] %s\n', response.error_type, response.error_msg);

%% Print out the results if available
if isfield(response, 'results') && ~isempty(response.results)
   results = response.results;
   fprintf('[%s] status %s: %s\n', response.service, results.msg_category, results.msg);
   fprintf('HED version: %s\n', results.schema_version);
   fprintf('Return data:\n%s\n', results.data);
end
