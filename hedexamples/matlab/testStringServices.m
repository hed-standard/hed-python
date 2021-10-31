%% Shows how to call hed-services to process a list of hedstrings.
% 
%  Example 1: Validate valid list of strings using HED version.
%
%  Example 2: Validate invalid list of strings using HED URL.
%
%  Example 3: Validate invalid list of strings uploading HED schema.
%
%  Example 4: Convert valid strings to long using HED version.
%
%% Setup requires a csrf_url and services_url. Must set header and options.
host = 'http://127.0.0.1:5000';
%host = 'https://hedtools.ucsd.edu/hed';
csrf_url = [host '/services']; 
services_url = [host '/services_submit'];
[cookie, csrftoken] = getSessionInfo(csrf_url);
header = ["Content-Type" "application/json"; ...
          "Accept" "application/json"; ...
          "X-CSRFToken" csrftoken; "Cookie" cookie];

options = weboptions('MediaType', 'application/json', 'Timeout', 120, ...
                     'HeaderFields', header);

%% Read in the schema text for the examples
schema_text = fileread('../data/schema_data/HED8.0.0.xml');
good_strings = {['Red,Blue'], ['Green'], ['White,Black']}; 
bad_strings = {['Red,Blue,Blech'], ['Green'], ['White,Black,Binge']}; 

%% Example 1: Validate valid list of strings using HED URL.
request1 = struct('service', 'strings_validate', ...
                  'schema_version', '8.0.0', ...
                  'string_list', '', ...
                  'check_warnings_validate', 'on');
request1.string_list = good_strings;
response1 = webwrite(services_url, request1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate a list of invalid strings. HED schema is URL.
myURL = ['https://raw.githubusercontent.com/hed-standard/' ...
         'hed-specification/master/hedxml/HED8.0.0.xml'];

request2 = struct('service', 'strings_validate', ...
                  'schema_url', myURL, ...
                  'string_list', '', ...
                  'check_warnings_validate', 'on');
request2.string_list = bad_strings;
response2 = webwrite(services_url, request2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Validate list of invalid strings uploading HED schema.
request3 = struct('service', 'strings_validate', ...
                  'schema_string', schema_text, ...
                  'string_list', '', ...
                  'check_warnings_validate', 'on');
request3.string_list = bad_strings;               
response3 = webwrite(services_url, request3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');

%% Example 4: Convert valid strings to long using HED version.
request4 = struct('service', 'strings_to_long', ...
                  'schema_version', '8.0.0', ...
                  'string_list', '');
request4.string_list = good_strings;               
response4 = webwrite(services_url, request4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
