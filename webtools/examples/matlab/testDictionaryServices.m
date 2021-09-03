%% Shows how to call hed-services to process a BIDS JSON sidecar.
% 
%  Example 1: Validate valid JSON sidecar using a HED version.
%
%  Example 2: Validate invalid JSON sidecar using HED URL.
%
%  Example 3: Convert valid JSON sidecar to long uploading HED schema.
%
%  Example 4: Convert valid JSON sidecar to short using a HED version.
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

%% Set up some data to use for the examples
json_text = fileread('../data/bids_events.json');
myURL = ['https://raw.githubusercontent.com/hed-standard/' ...
         'hed-specification/master/hedxml/HED7.2.0.xml'];
schema_text = fileread('../data/HED8.0.0.xml');

%% Example 1: Validate valid JSON sidecar using a HED version.
parameters = struct('schema_version', '8.0.0', ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata1 = struct('service', 'sidecar_validate', ...
                'service_parameters', parameters);
response1 = webwrite(services_url, sdata1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate invalid JSON sidecar using HED URL.
parameters = struct('schema_url', myURL, ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata2 = struct('service', 'sidecar_validate', ...
                'service_parameters', parameters);
response2 = webwrite(services_url, sdata2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Convert valid JSON sidecar to long uploading HED schema.
parameters = struct('schema_string', schema_text, ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata3 = struct('service', 'sidecar_to_long', ...
                'service_parameters', parameters);
response3 = webwrite(services_url, sdata3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');

%%  Example 4: Convert valid JSON sidecar to short using a HED version..
parameters = struct('schema_version', '8.0.0', ...
                    'json_string', json_text, ...
                    'check_for_warnings', true);
sdata4 = struct('service', 'sidecar_to_short', ...
                'service_parameters', parameters);
response4 = webwrite(services_url, sdata4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
 