function sample_texture_mcmc(inputs_HDF5_path, inputs_JSON_path, outputs_HDF5_path)
    allOpts = jsondecode(fileread(inputs_JSON_path));
    crystalSym = allOpts.crystal_symmetry;
    poleFigureDirections = allOpts.pole_figure_directions;
    max_samples = allOpts.max_samples;

    orientations = load_orientations_from_hdf(inputs_HDF5_path, crystalSym, poleFigureDirections);

    %% Calculate ODF
    try
        psi = SO3DeLaValleePoussinKernel('halfwidth', 7*degree);
    catch
        % `deLaValleePoussinKernel` is obselete since MTEX 5.9
        psi = deLaValleePoussinKernel('halfwidth', 7*degree);
    end
    odf = calcDensity(orientations, 'kernel', psi);

    %% Sample texture
    [~, sample] = MCMC_sampling(odf, psi, max_samples); % USE THIS FOR MODELS!

    export_orientations_HDF5(sample, outputs_HDF5_path);
end

function orientations = load_orientations_from_hdf(inputs_HDF5_path, crystalSym, poleFigureDirections)
    % as defined in MatFlow
    latticeDirs = {'a', 'b', 'c', 'a*', 'b*', 'c*'};
    reprQuatOrders = {'scalar-vector', 'vector-scalar'};

    align = h5readatt(inputs_HDF5_path, '/orientations', 'unit_cell_alignment');
    reprQuatOrderInt = h5readatt(inputs_HDF5_path, '/orientations', 'representation_quat_order');

    alignment = { ...
        sprintf('X||%s', latticeDirs{align(1) + 1}), ...
        sprintf('Y||%s', latticeDirs{align(2) + 1}), ...
        sprintf('Z||%s', latticeDirs{align(3) + 1}) ...
        };
    crystalSym = crystalSymmetry(crystalSym, alignment{:});
    oriQuatOrder = reprQuatOrders{reprQuatOrderInt + 1};

    millerDirs = cell(size(poleFigureDirections, 1));
    for i = 1:size(poleFigureDirections, 1)
        millerDirs{i} = Miller(num2cell(poleFigureDirections(i, :)), crystalSym);
    end

    data = h5read(inputs_HDF5_path, '/orientations/data');

    % TODO: why?
    data(2:end, :) = data(2:end, :) * -1;

    quat_data = quaternion(data);

    if strcmp(oriQuatOrder, 'vector-scalar')
        % Swap to scalar-vector order:
        quat_data = circshift(quat_data, 1, 2);
    end

    orientations = orientation(quat_data, crystalSym);
end


function [odf_rec, sample] = MCMC_sampling(odf, psi, max_samples)
    sample = [odf.discreteSample(1)];
    odf_rec = calcDensity(sample(1),'kernel',psi);
    min_error = calcError(odf,odf_rec);
    error_array = min_error;

    % Refinement: Add oris that reduce error
    start_time = timeofday(datetime);
    total_eval = 0;
    while length(sample) < max_samples

        % Add a sample only if it decreases the error.
        [sample, min_error, error_array] = update_samples(odf, psi, sample, min_error, error_array);

        total_eval = total_eval + 1;
        fprintf('n_samples:%d \terror:%f \n', length(sample), min_error);
    end

    odf_rec = calcDensity(sample,'kernel',psi);

    fprintf('Start: %s\n', start_time);
    fprintf('Finish: %s\n', timeofday(datetime));
    fprintf('Total evaluated: %d\n', total_eval);
end


function [samples,min_error,error_array] = update_samples(odf,psi,samples,min_error,error_array)
    % generate a single sample and add it to the samples
    sample = odf.discreteSample(1);

    % add the new sample to a temporary copy of the list
    temp_samples = [samples; sample];
    odf_rec = calcDensity(temp_samples, 'kernel', psi);
    error = calcError(odf, odf_rec);

    if error < min_error
        samples = temp_samples;
        min_error = error;

        % for sensitivity plot
        error_array(end+1) = min_error;
    end
end

function alignment = prepare_crystal_alignment(crystalSym)
    % as defined in MatFlow `LatticeDirection` enumeration class:
    keySet = {'a', 'b', 'c', 'a*', 'b*', 'c*'};
    valueSet = [0, 1, 2, 3, 4, 5];
    latticeDirs = containers.Map(keySet, valueSet);

    alignment = [];

    if isempty(crystalSym.alignment)
        % Cubic
        alignment(end + 1) = 0;
        alignment(end + 1) = 1;
        alignment(end + 1) = 2;
    else
        align1 = split(crystalSym.alignment{1}, '||');
        align2 = split(crystalSym.alignment{2}, '||');
        align3 = split(crystalSym.alignment{3}, '||');
        alignment(end + 1) = latticeDirs(align1{2});
        alignment(end + 1) = latticeDirs(align2{2});
        alignment(end + 1) = latticeDirs(align3{2});
    end

end


function export_orientations_HDF5(orientations, fileName)
    alignment = prepare_crystal_alignment(orientations.CS);
    ori_data = [orientations.a, orientations.b, orientations.c, orientations.d];

    % TODO: why?
    ori_data(:, 2:end) = ori_data(:, 2:end) * -1;

    ori_data = ori_data';
    h5create(fileName, '/orientations/data', size(ori_data));
    h5write(fileName, '/orientations/data', ori_data);
    h5writeatt(fileName, '/orientations', 'representation_type', 0);
    h5writeatt(fileName, '/orientations', 'representation_quat_order', 0);
    h5writeatt(fileName, '/orientations', 'unit_cell_alignment', alignment);
end
