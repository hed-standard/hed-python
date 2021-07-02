%% Shows how to call hed-services to process a list of hedstrings.
% 
%  Example 1: Validate a correct list of strings. HED schema is version.
%
%  Example 2: Validate an incorrect list of strings. HED schema is URL.
%
%  Example 3: Validate an incorrect list of strings. Upload HED schema.
%
%  Example 4: Convert valid strings to long. HED schema is version.
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
                 
%% Example 1: Validate a correct list of strings. HED schema is version.
sdata1 = get_input_template();
sdata1.service = 'string_validate';
sdata1.schema_version = '8.0.0-alpha.1';
sdata1.string_list = {['Red,Blue'], ['Green'], ['White,Black']}; 
response1 = webwrite(services_url, sdata1, options);
response1 = jsondecode(response1);
output_report(response1, 'Example 1 output');

%% Example 2: Validate an incorrect list of strings. HED schema is URL.
sdata2 = get_input_template();
sdata2.service = 'string_validate';
sdata2.schema_url = ['https://raw.githubusercontent.com/hed-standard/' ...
    'hed-specification/master/hedxml/HED8.0.0-alpha.1.xml'];
sdata2.string_list = {['Red,Blue,Blech'], ['Green'], ['White,Black,Binge']}; 
response2 = webwrite(services_url, sdata2, options);
response2 = jsondecode(response2);
output_report(response2, 'Example 2 output');

%% Example 3: Validate an incorrect list of strings. Upload HED schema.
sdata3 = get_input_template();
sdata3.service = 'string_validate';
sdata3.schema_url = ['https://raw.githubusercontent.com/hed-standard/' ...
    'hed-specification/master/hedxml/HED8.0.0-alpha.1.xml'];
sdata3.string_list = {['Red,Blue,Blech'], ['Green'], ['White,Black,Binge']}; 
response3 = webwrite(services_url, sdata3, options);
response3 = jsondecode(response3);
output_report(response3, 'Example 3 output');

%% Example 4: Convert valid strings to long. HED schema is version.
sdata4 = get_input_template();
sdata4.service = 'string_to_long';
schema_text = fileread('../data/HED8.0.0-alpha.1.xml');
sdata4.schema_string = schema_text;
sdata4.string_list = {['Red,Blue'], ['Green'], ['White,Black']}; 
response4 = webwrite(services_url, sdata4, options);
response4 = jsondecode(response4);
output_report(response4, 'Example 4 output');
