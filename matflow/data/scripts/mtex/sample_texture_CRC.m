function sample_texture_CRC(inputs_JSON_path, outputs_HDF5_path)

    rng(str2double(getenv('MATFLOW_RUN_RANDOM_SEED')));

    all_args = jsondecode(fileread(inputs_JSON_path));

    CRCFilePath = all_args.CRC_file_path;
    referenceFrameTransformation = all_args.EBSD_reference_frame_transformation;
    specimenSym = all_args.specimen_symmetry;
    phase = all_args.EBSD_phase;
    ebsdRotation = all_args.EBSD_rotation;
    numOrientations = all_args.num_orientations;
    kernelHalfwidthDeg = all_args.kernel_halfwidth_deg;
    eulerCorrection = [];
    if isfield(all_args, 'EBSD_euler_correction') && ~isempty(all_args.EBSD_euler_correction)
        value = all_args.EBSD_euler_correction;
        if ~isstruct(value) || ~isfield(value, 'euler_angles_deg')
            error('matflow:InvalidEulerCorrection', 'EBSD_euler_correction must specify euler_angles_deg.');
        end
        validateattributes(value.euler_angles_deg, {'numeric'}, {'real', 'vector', 'numel', 3, 'finite'}, mfilename, 'EBSD_euler_correction.euler_angles_deg');
        angles = num2cell(value.euler_angles_deg * degree);
        eulerCorrection = rotation.byEuler(angles{:});
    end

    validateattributes(numOrientations, {'numeric'}, {'real', 'scalar', 'finite', 'integer', 'positive'}, mfilename, 'num_orientations');
    validateattributes(kernelHalfwidthDeg, {'numeric'}, {'real', 'scalar', 'finite', '>', 0, '<=', 180}, mfilename, 'kernel_halfwidth_deg');

    numThreads = getenv('MATFLOW_RUN_NUM_THREADS');
    if ~isempty(numThreads)
        numThreads = str2double(numThreads);
        validateattributes(numThreads, {'numeric'}, {'real', 'scalar', 'finite', 'integer', 'positive'}, mfilename, 'MATFLOW_RUN_NUM_THREADS');
        maxNumCompThreads(numThreads);
    end

    EBSD_orientations = get_EBSD_orientations_from_CRC_file(CRCFilePath, referenceFrameTransformation, specimenSym, phase, ebsdRotation, eulerCorrection);
    ODF = calcDensity(EBSD_orientations, 'halfwidth', kernelHalfwidthDeg * degree);
    orientations = discreteSample(ODF, numOrientations);
    export_orientations_HDF5(orientations, outputs_HDF5_path);

end

function EBSD_orientations = get_EBSD_orientations_from_CRC_file(CRCFilePath, referenceFrameTransformation, specimenSym, phase, ebsdRotation, eulerCorrection)

    if ~isempty(eulerCorrection)
        % An explicit rotation takes precedence over legacy frame-selection options.
        referenceFrameTransformation = {'EulerCorrection', eulerCorrection};
    elseif isempty(referenceFrameTransformation)
        referenceFrameTransformation = {'EulerCorrection', rotation.id};
    else
        switch referenceFrameTransformation
            case {'euler_to_spatial', 'convertEuler2SpatialReferenceFrame'}
                referenceFrameTransformation = {'convertEuler2SpatialReferenceFrame'};
            case {'spatial_to_euler', 'convertSpatial2EulerReferenceFrame'}
                referenceFrameTransformation = {'EulerCorrection', rotation.id};
            otherwise
                error('matflow:InvalidReferenceFrame', 'Unknown EBSD reference frame transformation: %s', referenceFrameTransformation);
        end
    end

    ebsd = loadEBSD_crc(CRCFilePath, referenceFrameTransformation{:});
    if ~isempty(eulerCorrection) && ~ismember('EulerCorrection', properties(class(ebsd)))
        % MTEX 6.x ignores EulerCorrection; its unflagged reader leaves angles alone.
        ebsd = rotate(ebsd, eulerCorrection, 'keepXY');
    end

    if ~isempty(ebsdRotation)
        % Note that using rotate appears to remove the non-indexed phase.
        validateattributes(ebsdRotation.euler_angles_deg, {'numeric'}, {'real', 'vector', 'numel', 3, 'finite'}, mfilename, 'EBSD_rotation.euler_angles_deg');
        rotationEulersRad = num2cell(ebsdRotation.euler_angles_deg * degree);
        rot = rotation.byEuler(rotationEulersRad{:});

        keepXY = isfield(ebsdRotation, 'keep_XY') && ebsdRotation.keep_XY;
        keepEuler = isfield(ebsdRotation, 'keep_euler') && ebsdRotation.keep_euler;
        if keepXY && keepEuler
            error('matflow:InvalidRotation', 'EBSD_rotation.keep_XY and keep_euler cannot both be true.');
        elseif keepXY
            ebsd = rotate(ebsd, rot, 'keepXY');
        elseif keepEuler
            ebsd = rotate(ebsd, rot, 'keepEuler');
        else
            ebsd = rotate(ebsd, rot);
        end

    end

    EBSD_orientations = ebsd(phase).orientations;
    oriData = [EBSD_orientations.a, EBSD_orientations.b, EBSD_orientations.c, EBSD_orientations.d];
    if isempty(oriData) || any(~isfinite(oriData(:)))
        error('matflow:InvalidPhaseOrientations', 'Phase %s has no finite indexed orientations.', phase);
    end
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
