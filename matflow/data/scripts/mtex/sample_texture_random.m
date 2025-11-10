function sample_texture_random(inputs_JSON_path, outputs_HDF5_path)
    all_args = jsondecode(fileread(inputs_JSON_path));

    crystal_symmetry = all_args.crystal_symmetry;
    specimen_symmetry = all_args.specimen_symmetry;
    num_orientations = all_args.num_orientations;

    ODF = get_random_ODF(crystal_symmetry, specimen_symmetry, num_orientations);
    orientations = discreteSample(ODF, num_orientations);
    export_orientations_HDF5(orientations, outputs_HDF5_path);

end

function ODF = get_random_ODF(crystal_symmetry, specimen_symmetry, num_orientations)
    crystalSym = crystalSymmetry(crystal_symmetry);
    specimenSym = specimenSymmetry(specimen_symmetry);
    ori = orientation.rand(num_orientations, crystalSym, specimenSym);
    ODF = calcDensity(ori);
end

function export_orientations_HDF5(orientations, fileName)
    alignment = prepare_crystal_alignment(orientations.CS);
    ori_data = [orientations.a, orientations.b, orientations.c, orientations.d];
    ori_data = ori_data';
    
    % TODO: why?
    ori_data(:, 2:end) = ori_data(:, 2:end) * -1;

    h5create(fileName, '/orientations/data', size(ori_data));
    h5write(fileName, '/orientations/data', ori_data);
    h5writeatt(fileName, '/orientations', 'representation_type', 0);
    h5writeatt(fileName, '/orientations', 'representation_quat_order', 0);
    h5writeatt(fileName, '/orientations', 'unit_cell_alignment', alignment);
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
