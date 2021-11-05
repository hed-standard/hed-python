%% Shows how to call hed-services to process a spreadsheet of event tags.
% 
%  Example 1: Validate valid spreadsheet file using schema version.
%
%  Example 2: Validate invalid spreadsheet file using HED URL.
%
%  Example 3: Convert valid spreadsheet file to long uploading HED schema.
%
%  Example 4: Convert valid spreadsheet file to short using HED version.
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

%% Set the data used in the examples
spreadsheet_text_HED3 = fileread('../data/spreadsheet_data/LKTEventCodesHED3.tsv');
spreadsheet_text_HED2 = fileread('../data/spreadsheet_data/LKTEventCodesHED2.tsv');
schema_text = fileread('../data/schema_data/HED8.0.0.xml');
labelPrefix = 'Property/Informational-property/Label/';
descPrefix = 'Property/Informational-property/Description/';
schema_url =['https://raw.githubusercontent.com/hed-standard/' ...
             'hed-specification/master/hedxml/HED7.2.0.xml'];
         
%% Example 1: Validate valid spreadsheet file using schema version.
request1 = struct('service', 'spreadsheet_validate', ...
                  'schema_version', '7.2.0', ...
                  'spreadsheet_string', spreadsheet_text_HED2, ...
                  'check_warnings_validate', 'on', ...
                  'has_column_names', 'on', ...
                  'column_2_input', 'Event/Label/', ...
                  'column_2_check', 'on', ...
                  'column_5_input', '', ...
                  'column_5_check', 'on');
response1 = webwrite(services_url, request1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate invalid spreadsheet file using HED URL.
request2 = struct('service', 'spreadsheet_validate', ...
                  'schema_url', schema_url, ...
                  'spreadsheet_string', spreadsheet_text_HED3, ...
                  'check_warnings_validate', 'on', ...
                  'has_column_names', 'on', ...
                  'column_2_input', 'Event/Label/', ...
                  'column_2_check', 'on', ...
                  'column_5_input', '', ...
                  'column_5_check', 'on');
response2 = webwrite(services_url, request2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Convert valid spreadsheet file to long uploading HED schema.
request3 = struct('service', 'spreadsheet_to_long', ...
                  'schema_string', schema_text, ...
                  'spreadsheet_string', spreadsheet_text_HED3, ...
                  'check_warnings_validate', 'on', ...
                  'has_column_names', 'on', ...
                  'column_2_input', labelPrefix, ...
                  'column_2_check', 'on', ...
                  'column_4_input', descPrefix, ...
                  'column_4_check', 'on', ...
                  'column_5_input', '', ...
                  'column_5_check', 'on');
response3 = webwrite(services_url, request3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');
results = response3.results;

%% Example 4: Convert valid spreadsheet file to short using uploaded HED.
request4 = struct('service', 'spreadsheet_to_short', ...
                  'schema_string', schema_text, ...
                  'spreadsheet_string', spreadsheet_text_HED3, ...
                  'has_column_names', 'on', ...
                  'column_2_input', labelPrefix, ...
                  'column_2_check', 'on', ...
                  'column_4_input', descPrefix, ...
                  'column_4_check', 'on', ...
                  'column_5_input', '', ...
                  'column_5_check', 'on');
response4 = webwrite(services_url, request4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
