function combine_orientations_from_CRC_files(inputs_JSON_path, outputs_HDF5_path)

    args = jsondecode(fileread(inputs_JSON_path));
    CRC_file_paths = args.CRC_file_paths;
    phi_corrections = args.phi_corrections;

    CS = crystalSymmetry('m-3m', [4.04 4.04 4.04], 'mineral', 'Aluminum', 'color', [0 0.8 1]);

    % load, correct, check maps
    corrected_maps = cell(length(CRC_file_paths), 1);
    for m=1:length(CRC_file_paths)
        disp(CRC_file_paths(m))
        disp(phi_corrections(m,:))
        corrected_maps{m} = loadmap_correct(CRC_file_paths(m), CS, phi_corrections(m,:));
    end

    %% Combine EBSD maps data
    combined_EBSD = combine_maps(corrected_maps);

    %% Rotate combined data - OPTIONAL
    angle = 0;
    rotz = rotation('axis', zvector, 'angle', angle*degree);
    rotated_EBSD = rotate(combined_EBSD, rotz, 'keepXY');

    export_orientations_HDF5(rotated_EBSD.orientations, outputs_HDF5_path);
end

% "get_EBSD_orientations_from_CRC_file" used elsewhere in MatFlow only seems to be able to do one rotation
% Passing in a vector of 3 euler angles makes the rotation function crash.
function correctedmap = loadmap_correct(filepath, CS, correction)
    ebsdmap = EBSD.load(filepath,CS,'interface','crc','convertSpatial2EulerReferenceFrame', 'Bunge');
    correctedmap = apply_corrections(ebsdmap('Aluminum'), correction);
end

function combined_EBSD = combine_maps(corrected_maps)
    % concat each onto array
    combined_EBSD = [];
    for m=1:length(corrected_maps)
        map = corrected_maps{m};
        combined_EBSD = [combined_EBSD, map];
    end
end

function corrected_EBSD_map = apply_corrections(EBSD_map, correction)
    rotz = rotation('axis',zvector,'angle',correction(1)*degree);
    EBSD_map = rotate(EBSD_map,rotz,'keepXY');
    rotx = rotation('axis',xvector,'angle',correction(2)*degree);
    EBSD_map = rotate(EBSD_map,rotx,'keepXY');
    rotz2 = rotation('axis',zvector,'angle',correction(3)*degree);
    corrected_EBSD_map = rotate(EBSD_map,rotz2,'keepXY');
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
