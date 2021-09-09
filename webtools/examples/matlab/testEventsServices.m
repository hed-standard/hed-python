%% Shows how to call hed-services to process a BIDS events file.
% 
%  Example 1: Validate valid events file using HED version.
%
%  Example 2: Validate invalid events file using a HED URL.
%
%  Example 3: Assemble valid events file uploading HED schema.
%
%  Example 4: Assemble valid events file (def expand) using HED version.
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

%% Read the JSON sidecar into a string for all examples
json_text = fileread('../data/bids_events.json');
events_text = fileread('../data/bids_events.tsv');
schema_text = fileread('../data/HED8.0.0.xml');
myURL = ['https://raw.githubusercontent.com/hed-standard/' ...
         'hed-specification/master/hedxml/HED7.2.0.xml'];
     
%% Example 1: Validate valid events file using HED version.
parameters = struct('schema_version', '8.0.0', ...
                    'json_string', json_text, ...
                    'events_string', events_text, ...
                    'check_for_warnings_validate', true, ...
                    'defs_expand', false);
sdata1 = struct('service', 'events_validate', ...
                'service_parameters', parameters);
response1 = webwrite(services_url, sdata1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate invalid events file using a HED URL.
parameters = struct('schema_url', myURL, ...
                    'json_string', json_text, ...
                    'events_string', events_text, ...
                    'check_for_warnings_validate', true, ...
                    'defs_expand', false);
sdata2 = struct('service', 'events_validate', ...
                'service_parameters', parameters);
response2 = webwrite(services_url, sdata2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Assemble valid events file uploading a HED schema
parameters = struct('schema_string', schema_text, ...
                    'json_string', json_text, ...
                    'events_string', events_text, ...
                    'check_for_warnings_assemble', true, ...
                    'defs_expand', false);
sdata3 = struct('service', 'events_assemble', ...
                'service_parameters', parameters);
response3 = webwrite(services_url, sdata3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');

%%  Example 4: Assemble valid events file (def expand) using HED version.
parameters = struct('schema_version', '8.0.0', ...
                    'json_string', json_text, ...
                    'events_string', events_text, ...
                    'check_for_warnings_assemble', true, ...
                    'defs_expand', true);
sdata4 = struct('service', 'events_assemble', ...
                'service_parameters', parameters);
response4 = webwrite(services_url, sdata4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');