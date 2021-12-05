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
json_text = fileread('../data/wakeman_henson_data/task-FacePerception_events.json');
myURL = ['https://raw.githubusercontent.com/hed-standard/' ...
         'hed-specification/master/hedxml/HED7.2.0.xml'];
schema_text = fileread('../data/schema_data/HED8.0.0.xml');

%% Example 1: Validate valid JSON sidecar using a HED version.
request1 = struct('service', 'sidecar_validate', ...
                 'schema_version', '8.0.0', ...
                 'json_string', json_text, ...
                 'check_warnings_validate', 'on');
response1 = webwrite(services_url, request1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate invalid JSON sidecar using HED URL.
request2 = struct('service', 'sidecar_validate', ...
                  'json_string', json_text, ...
                  'schema_url', myURL, ...    
                  'check_warnings_validate', 'on');
response2 = webwrite(services_url, request2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Convert valid JSON sidecar to long uploading HED schema.
request3 = struct('service', 'sidecar_to_long', ...
                  'schema_string', schema_text, ...
                  'json_string', json_text, ...
                  'check_warnings_validate', 'on');

response3 = webwrite(services_url, request3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');

%%  Example 4: Convert valid JSON sidecar to short using a HED version..
request4 = struct('service', 'sidecar_to_short', ...
                  'schema_version', '8.0.0', ...
                  'json_string', json_text, ...
                  'check_warnings_validate', 'on');
response4 = webwrite(services_url, request4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
 