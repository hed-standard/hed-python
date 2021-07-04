%% Shows how to call hed-services to process a BIDS events file.
% 
%  Example 1: Validate a correct events file. HED schema is version.
%
%  Example 2: Validate an incorrect events. HED schema is URL.
%
%  Example 3: Assemble a valid events file. Upload HED schema.
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
json_text = fileread('../data/good_dictionary.json');
events_text = fileread('../data/good_events.tsv');

%% Example 1: Validate a correct events file. HED schema is version.
sdata1 = get_input_template();
sdata1.service = 'events_validate';
sdata1.schema_version = '8.0.0-alpha.1';
sdata1.json_string = json_text;
sdata1.events_string = events_text;
response1 = webwrite(services_url, sdata1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate an incorrect events file. HED schema is URL.
sdata2 = get_input_template();
sdata2.service = 'events_validate';
sdata2.schema_url = ['https://raw.githubusercontent.com/hed-standard/' ...
    'hed-specification/master/hedxml/HED7.2.0.xml'];
sdata2.json_string = json_text; 
sdata2.events_string = events_text;
response2 = webwrite(services_url, sdata2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Assemble a valid events file. Upload HED schema.
sdata3 = get_input_template();
sdata3.service = 'events_assemble';
sdata3.schema_url = ['https://raw.githubusercontent.com/hed-standard/' ...
    'hed-specification/master/hedxml/HED8.0.0-alpha.1.xml'];
sdata3.json_string = json_text; 
sdata3.events_string = events_text;
response3 = webwrite(services_url, sdata3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');

%%  Example 4: Assemble valid events file with exp defs. HED schema is version.
sdata4 = get_input_template();
sdata4.service = 'events_assemble';
schema_text = fileread('../data/HED8.0.0-alpha.1.xml');
sdata4.schema_string = schema_text;
sdata4.json_string = json_text; 
sdata4.events_string = events_text;
sdata4.defs_expand = true;
response4 = webwrite(services_url, sdata4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
 
