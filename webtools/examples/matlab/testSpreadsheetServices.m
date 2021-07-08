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

%% Read the JSON dictionary into a string for all examples
spreadsheet_text = fileread('../data/LKTEventCodes8Beta3.tsv');
schema_text = fileread('../data/HED8.0.0-beta.3.xml');

%% Example 1: Validate valid spreadsheet file using schema version.
sdata1 = get_input_template();
sdata1.service = 'spreadsheet_validate';
sdata1.schema_version = '8.0.0-beta.3';
sdata1.spreadsheet_string = spreadsheet_text;
sdata1.column_2_input = 'Attribute/Informational/Label/';
sdata1.column_2_check = 'on';
sdata1.column_4_input = 'Attribute/Informational/Description/';
sdata1.column_4_check = 'on';
sdata1.column_5_input = '';
sdata1.column_5_check = 'on';
sdata1.has_column_names = true;
response1 = webwrite(services_url, sdata1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate invalid spreadsheet file using HED URL.
sdata2 = get_input_template();
sdata2.service = 'spreadsheet_validate';
sdata2.schema_url =['https://raw.githubusercontent.com/hed-standard/' ...
    'hed-specification/master/hedxml/HED7.2.0.xml'];
sdata2.spreadsheet_string = spreadsheet_text;
sdata2.column_2_input = 'Event/Label/';
sdata2.column_2_check = 'on';
sdata2.column_4_input = 'Event/Description/';
sdata2.column_4_check = 'on';
sdata2.column_5_input = '';
sdata2.column_5_check = 'on';
sdata2.has_column_names = true;
response2 = webwrite(services_url, sdata2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Convert valid spreadsheet file to long uploading HED schema.
sdata3 = get_input_template();
sdata3.service = 'spreadsheet_to_long';
sdata3.schema_string = schema_text;
sdata3.spreadsheet_string = spreadsheet_text;
sdata3.column_2_input = 'Attribute/Informational/Label/';
sdata3.column_2_check = 'on';
sdata3.column_4_input = 'Attribute/Informational/Description/';
sdata3.column_4_check = 'on';
sdata3.column_5_input = '';
sdata3.column_5_check = 'on';
sdata3.has_column_names = true;
response3 = webwrite(services_url, sdata3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');
results = response3.results;
%% Example 4: Convert valid spreadsheet file to short using HED version..
sdata4 = get_input_template();
sdata4.service = 'spreadsheet_to_short';
sdata4.schema_version = '8.0.0-beta.3';
sdata4.spreadsheet_string = spreadsheet_text;
sdata4.column_2_input = 'Attribute/Informational/Label/';
sdata4.column_2_check = 'on';
sdata4.column_4_input = 'Attribute/Informational/Description/';
sdata4.column_4_check = 'on';
sdata4.column_5_input = '';
sdata4.column_5_check = 'on';
sdata4.has_column_names = true;
response4 = webwrite(services_url, sdata3, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
