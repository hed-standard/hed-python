function [] = showServices(result)

if ~isfield(result, 'supported_services')
    fprintf('No supported_services field found in result\n');
    return;
end
services = result.supported_services;
fields = fieldnames(services);
fprintf('Services:\n');
for k = 1:length(fields)
    info = services.(fields{k});
    fprintf('  %s  [%s]\n', info.Name, info.Description);
    showParameters(info.Parameters)
    showReturnValues(info.Returns);
end


function showParameters(params)
    if isempty(params)
        return;
    end
    fprintf('      Parameters:\n');
    for p = 1:length(params)
        fprintf('         %s [%s]\n', params(p).Name, params(p).Description);
    end
    
function showReturnValues(returns)
    if isempty(returns)
        return;
    end
    fprintf('      Returns:\n');
    for p = 1:length(returns)
        fprintf('         %s [%s]\n', returns(p).Name, returns(p).Description);
    end