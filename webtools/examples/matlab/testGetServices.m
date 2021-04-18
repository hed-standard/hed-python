%% Shows how to call hed-services to obtain a list of services
host = 'http://127.0.0.1:5000';
%host = 'https://hedtools.ucsd.edu/hed';
csrf_url = [host '/hed-services']; 
services_url = [host '/hed-services-submit'];

%% Send an empty request to get the CSRF TOKEN and the session cookie
[cookie, csrftoken] = getSessionInfo(csrf_url);

%% Set the header and weboptions
header = ["Content-Type" "application/json"; ...
          "Accept" "application/json"; ...
          "X-CSRFToken" csrftoken; ...
          "Cookie" cookie];

options = weboptions('MediaType', 'application/json', 'Timeout', 60, ...
                     'HeaderFields', header);
data = struct();
data.service = 'get_services';
data.hed_version = '7.1.2';
data.check_for_warnings = true;

%% Send the request and get the response
response = webwrite(services_url, data, options);
response = jsondecode(response);
result = response.result;
if isfield(response, 'error_type')
    error_type = response.error_type;
else
    error_type = '';
end
if isfield(response, 'message')
    message = response.message;
else
    message = '';
end

showServices(result)

fprintf('Error report: [%s] %s\n', error_type, message)

