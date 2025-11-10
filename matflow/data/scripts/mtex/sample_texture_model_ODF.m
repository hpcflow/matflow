function sample_texture_model_ODF(inputs_JSON_path, outputs_HDF5_path)

    all_args = jsondecode(fileread(inputs_JSON_path));

    numOrientations = all_args.num_orientations;
    crystalSym = all_args.crystal_symmetry;
    specimenSym = all_args.specimen_symmetry;

    % Note, for this to work in a consistent way, the objects in the array
    % of ODF component should each have a distinct key. Otherwise,
    % `jsondecode` will load the array into a structure array.
    ODFComponentsDefns = all_args.ODF_components;

    % Normalise `jsondecode`'s "helpful" parsing in the case where there
    % is just one object in the array of ODF components:
    if isstruct(ODFComponentsDefns)
        ODFComponentsDefns = {ODFComponentsDefns};
    end

    ODF = get_model_ODF(ODFComponentsDefns, crystalSym, specimenSym);
    orientations = discreteSample(ODF, numOrientations);
    export_orientations_HDF5(orientations, outputs_HDF5_path);

end

function kernel = get_DeLaValleePoussin_kernel(halfwidth_deg)
    % `deLaValleePoussinKernel` is obselete since MTEX 5.9
    try
        kernel = SO3DeLaValleePoussinKernel('halfwidth', halfwidth_deg * degree);
    catch
        kernel = deLaValleePoussinKernel('halfwidth', halfwidth_deg * degree);
    end

end

function ODF = get_model_ODF(ODFComponentsDefns, crystalSym, specimenSym)

    crystalSym = crystalSymmetry(crystalSym);
    specimenSym = specimenSymmetry(specimenSym);

    for i = 1:length(ODFComponentsDefns)

        comp = ODFComponentsDefns{i};

        if strcmp(comp.type, 'unimodal')
            kernel = get_DeLaValleePoussin_kernel(comp.halfwidth);

            if isfield(comp, 'modal_orientation_HKL')
                modalOri = orientation.byMiller( ...
                    comp.modal_orientation_HKL.', ...
                    comp.modal_orientation_UVW.', ...
                    crystalSym, ...
                    specimenSym ...
                );

            elseif isfield(comp, 'modal_orientation_euler')
                euler_deg = num2cell(comp.modal_orientation_euler * degree);
                modalOri = orientation.byEuler(euler_deg{:}, crystalSym, specimenSym);

            end

            ODFComponent = unimodalODF(modalOri, kernel);

        elseif strcmp(comp.type, 'uniform')
            ODFComponent = uniformODF(crystalSym, specimenSym);

        elseif strcmp(comp.type, 'fibre')
            kernel = get_DeLaValleePoussin_kernel(comp.halfwidth);

            if isfield(comp, 'mtexfibre')

                if strcmp(comp.mtexfibre, 'alpha')
                    ODFComponent = fibreODF(fibre.alpha(crystalSym, specimenSym), kernel);

                elseif strcmp(comp.mtexfibre, 'beta')
                    ODFComponent = fibreODF(fibre.beta(crystalSym, specimenSym), kernel);

                elseif strcmp(comp.mtexfibre, 'epsilon')
                    ODFComponent = fibreODF(fibre.epsilon(crystalSym, specimenSym), kernel);

                elseif strcmp(comp.mtexfibre, 'eta')
                    ODFComponent = fibreODF(fibre.eta(crystalSym, specimenSym), kernel);

                elseif strcmp(comp.mtexfibre, 'fit')
                    ODFComponent = fibreODF(fibre.fit(crystalSym, specimenSym), kernel);

                elseif strcmp(comp.mtexfibre, 'gamma')
                    ODFComponent = fibreODF(fibre.gamma(crystalSym, specimenSym), kernel);

                elseif strcmp(comp.mtexfibre, 'rand')
                    ODFComponent = fibreODF(fibre.rand(crystalSym, specimenSym), kernel);

                elseif strcmp(comp.mtexfibre, 'tau')
                    ODFComponent = fibreODF(fibre.tau(crystalSym, specimenSym), kernel);
                end

            elseif isfield(comp, 'fibreCrystalDir')

                fibreCrystalDir = num2cell(comp.fibreCrystalDir);
                f = fibre( ...
                    Miller(fibreCrystalDir{:}, crystalSym), ...
                    vector3d.(upper(comp.fibreSpecimenDir)) ...
                );
                ODFComponent = fibreODF(f, kernel);

            end

        end

        if i == 1
            ODF = comp.component_fraction * ODFComponent;
        else
            ODF = ODF + (comp.component_fraction * ODFComponent);
        end

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
