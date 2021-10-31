%% Shows how to call hed-services to obtain a list of services
host = 'http://127.0.0.1:5000';
%host = 'https://hedtools.ucsd.edu/hed';
csrf_url = [host '/services']; 
services_url = [host '/services_submit'];

%% Send an empty request to get the CSRF TOKEN and the session cookie
[cookie, csrftoken] = getSessionInfo(csrf_url);

%% Set the header and weboptions
header = ["Content-Type" "application/json"; ...
          "Accept" "application/json"; ...
          "X-CSRFToken" csrftoken; ...
          "Cookie" cookie];

options = weboptions('MediaType', 'application/json', 'Timeout', 60, ...
                     'HeaderFields', header);

%% Send the request and get the response
data = struct('service', 'get_services', 'service_parameters', '');
response = webwrite(services_url, data, options);
response = jsondecode(response);
fprintf('Error report:  [%s] %s\n', response.error_type, response.error_msg);

%% Print out the results if available
if isfield(response, 'results') && ~isempty(response.results)
   results = response.results;
   fprintf('[%s] status %s: %s\n', response.service, results.msg_category, results.msg);
   fprintf('Return data:\n%s\n', results.data);
end