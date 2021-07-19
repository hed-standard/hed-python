%% Shows how to call hed-services to process a BIDS JSON dictionary.
% 
%  Example 1: Validate valid JSON dictionary using a HED version.
%
%  Example 2: Validate invalid JSON dictionary using HED URL.
%
%  Example 3: Convert valid JSON dictionary to long uploading HED schema.
%
%  Example 4: Convert valid JSON dictionary to short using a HED version.
%
%% Setup requires a csrf_url and services_url. Must set header and options.
host = 'http://127.0.0.1:5000';
%host = 'https://hedtools.ucsd.edu/hed';
csrf_url = [host '/services']; 
services_url = [host '/services_submit'];
[cookie, csrftoken] = getSessionInfo(csrf_url);
header = ["Content-Type" "application/json"; ...
          "Accept" "application/json"; 
          "X-CSRFToken" csrftoken; "Cookie" cookie];

options = weboptions('MediaType', 'application/json', 'Timeout', 120, ...
                     'HeaderFields', header);

%% Read the JSON dictionary into a string for all examples
json_text = fileread('../data/good_dictionary.json');

%% Example 1: Validate valid JSON dictionary using a HED version.
sdata1 = struct('service', 'dictionary_validate', 'service_parameters', []);
parameters = struct('schema_version', '8.0.0-alpha.1', ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata1.service_parameters = parameters;
response1 = webwrite(services_url, sdata1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate invalid JSON dictionary using HED URL.
myURL = ['https://raw.githubusercontent.com/hed-standard/' ...
         'hed-specification/master/hedxml/HED7.2.0.xml'];
sdata2 = struct('service', 'dictionary_validate', 'service_parameters', []);
parameters = struct('schema_url', myURL, ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata2.service_parameters = parameters;
response2 = webwrite(services_url, sdata2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Convert valid JSON dictionary to long uploading HED schema.
mySchema = fileread('../data/HED8.0.0-alpha.1.xml');
sdata3 = struct('service', 'dictionary_to_long', 'service_parameters', []);
parameters = struct('schema_string', mySchema, ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata3.service_parameters = parameters;
response3 = webwrite(services_url, sdata3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');

%%  Example 4: Convert valid JSON dictionary to short using a HED version..
sdata4 = struct('service', 'dictionary_to_short', 'service_parameters', []);
parameters = struct('schema_version', '8.0.0-alpha.1', ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata4.service_parameters = parameters;
response4 = webwrite(services_url, sdata4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
 