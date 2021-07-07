%% Shows how to call hed-services to process a spreadsheet of event tags.
% 
%  Example 1: Validate a correct spreadsheet file. HED schema is file.
%
%  Example 2: Validate an incorrect spreadsheet file. HED schema is URL.
%
%  Example 3: Convert valid spreadsheet file to long. HED schema is file.
%
%  Example 4: Assemble a valid events file (def expand). HED schema is version.
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

%% Example 1: Validate a correct events file. HED schema is version.
sdata1 = get_input_template();
sdata1.service = 'spreadsheet_validate';
sdata1.schema_string = schema_text;
sdata1.spreadsheet_string = spreadsheet_text;
sdata1.Column_2_input = 'Attribute/Informational/Label/';
sdata1.Column_2_check = 'on';
sdata1.Column_4_input = 'Attribute/Informational/Description/';
sdata1.Column_4_check = 'on';
sdata1.Column_5_input = '';
sdata1.Column_5_check = 'on';
sdata1.has_column_names = true;
response1 = webwrite(services_url, sdata1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');


%% Example 2: Validate an incorrect spreadsheet file. HED schema is URL.
sdata2 = get_input_template();
sdata2.service = 'spreadsheet_validate';
sdata2.schema_url =['https://raw.githubusercontent.com/hed-standard/' ...
    'hed-specification/master/hedxml/HED7.2.0.xml'];
sdata2.spreadsheet_string = spreadsheet_text;
sdata2.Column_2_input = 'Event/Label/';
sdata2.Column_2_check = 'on';
sdata2.Column_4_input = 'Event/Description/';
sdata2.Column_4_check = 'on';
sdata2.Column_5_input = '';
sdata2.Column_5_check = 'on';
sdata2.has_column_names = true;
response2 = webwrite(services_url, sdata2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

% sdata2 = get_input_template();
% sdata2.service = 'events_validate';
% sdata2.schema_url = ['https://raw.githubusercontent.com/hed-standard/' ...
%     'hed-specification/master/hedxml/HED7.2.0.xml'];
% sdata2.json_string = json_text; 
% sdata2.events_string = events_text;
% response2 = webwrite(services_url, sdata2, options);
% response2 = jsondecode(response2);
% output_report(response2, 'Example 2 output');
% 
% %% Example 3: Assemble a valid events file. Upload HED schema.
% sdata3 = get_input_template();
% sdata3.service = 'events_assemble';
% sdata3.schema_url = ['https://raw.githubusercontent.com/hed-standard/' ...
%     'hed-specification/master/hedxml/HED8.0.0-alpha.1.xml'];
% sdata3.json_string = json_text; 
% sdata3.events_string = events_text;
% response3 = webwrite(services_url, sdata3, options);
% response3 = jsondecode(response3);
% output_report(response3, 'Example 3 output');
% 
% %%  Example 4: Assemble valid events file with exp defs. HED schema is version.
% sdata4 = get_input_template();
% sdata4.service = 'events_assemble';
% schema_text = fileread('../data/HED8.0.0-alpha.1.xml');
% sdata4.schema_string = schema_text;
% sdata4.json_string = json_text; 
% sdata4.events_string = events_text;
% sdata4.defs_expand = true;
% response4 = webwrite(services_url, sdata4, options);
% response4 = jsondecode(response4);
% output_report(response4, 'Example 4 output');
%  
