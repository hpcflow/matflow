function sample_orientations_CTF(inputs_JSON_path, outputs_HDF5_path)

    all_args = jsondecode(fileread(inputs_JSON_path));

    CTFFilePath = all_args.CTF_file_path;
    referenceFrameTransformation = all_args.EBSD_reference_frame_transformation;
    specimenSym = all_args.specimen_symmetry;
    phase = all_args.EBSD_phase;
    rotation = all_args.EBSD_rotation;
    numOrientations = all_args.num_orientations;

    EBSD_orientations = get_EBSD_orientations_from_CTF_file(CTFFilePath, referenceFrameTransformation, specimenSym, phase, rotation);
    orientations = EBSD_orientations(randperm(EBSD_orientations.length, numOrientations));
    export_orientations_HDF5(orientations, outputs_HDF5_path);

end

function EBSD_orientations = get_EBSD_orientations_from_CTF_file(CTFFilePath, referenceFrameTransformation, specimenSym, phase, rotation)

    if isempty(referenceFrameTransformation)
        referenceFrameTransformation = {};
    else
        referenceFrameTransformation = {referenceFrameTransformation};
    end

    ebsd = loadEBSD_ctf(CTFFilePath, referenceFrameTransformation{:});

    if ~isempty(rotation)
        % Note that using rotate appears to remove the non-indexed phase.
        rotationEulersRad = num2cell(rotation.euler_angles_deg * degree);
        rot = rotation('euler', rotationEulersRad{:});

        if isfield(rotation, 'keep_XY')
            ebsd = rotate(ebsd, rot, 'keepXY');
        elseif isfield(rotation, 'keep_euler')
            ebsd = rotate(ebsd, rot, 'keepEuler');
        else
            ebsd = rotate(ebsd, rot);
        end

    end

    EBSD_orientations = ebsd(phase).orientations;
    EBSD_orientations.SS = specimenSymmetry(specimenSym);
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
