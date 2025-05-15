function exitcode = plot_inverse_pole_figures(inputs_HDF5_path, inputs_JSON_path)

    allOpts = jsondecode(fileread(inputs_JSON_path));
    crystalSym = allOpts.crystal_symmetry;
    
    useContours = allOpts.use_contours;
    plotIPFKey = allOpts.plot_IPF_key;
    IPFRefDirs = allOpts.IPF_reference_directions;
    
    % as defined in MatFlow
    latticeDirs = {'a', 'b', 'c', 'a*', 'b*', 'c*'};
    reprTypes = {'quaternion', 'euler'};
    reprQuatOrders = {'scalar-vector', 'vector-scalar'};
    
    align = h5readatt(inputs_HDF5_path, '/orientations', 'unit_cell_alignment');
    reprTypeInt = h5readatt(inputs_HDF5_path, '/orientations', 'representation_type');
    reprQuatOrderInt = h5readatt(inputs_HDF5_path, '/orientations', 'representation_quat_order');
    
    alignment = { ...
                     sprintf('X||%s', latticeDirs{align(1) + 1}), ...
                     sprintf('Y||%s', latticeDirs{align(2) + 1}), ...
                     sprintf('Z||%s', latticeDirs{align(3) + 1}) ...
                 };
    crystalSym = crystalSymmetry(crystalSym, alignment{:});
    oriType = reprTypes{reprTypeInt + 1};
    oriQuatOrder = reprQuatOrders{reprQuatOrderInt + 1};
    
    refDirs = vector3d.(upper(IPFRefDirs{1}));
    for i = 2:size(IPFRefDirs, 1)        
        refDirs = [refDirs, vector3d.(upper(IPFRefDirs{i}))];
    end
    
    data = h5read(inputs_HDF5_path, '/orientations/data');

    % TODO: why?
    data(2:end, :) = data(2:end, :) * -1;

    quat_data = quaternion(data);
    
    if strcmp(oriQuatOrder, 'vector-scalar')
        % Swap to scalar-vector order:
        quat_data = circshift(quat_data, 1, 2);
    end
    
    if plotIPFKey
        ipfKey = ipfColorKey(crystalSym);
        plot(ipfKey);
        saveFigure('IPF_key.png');
    end
    
    orientations = orientation(quat_data, crystalSym);
    
    if useContours
        plotIPDF(orientations,refDirs,'contourf');
    else
        plotIPDF(orientations,refDirs);
    end
    
    saveFigure('inverse_pole_figure.png');

    close all;

    exitcode = 1;
end
