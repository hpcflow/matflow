function exitcode = plot_pole_figures(inputs_HDF5_path, inputs_JSON_path)

    allOpts = jsondecode(fileread(inputs_JSON_path));
    crystalSym = allOpts.crystal_symmetry;    
    useContours = allOpts.use_contours;
    plot_IPFKey = allOpts.plot_IPF_key;
    poleFigureDirections = allOpts.pole_figure_directions;
    IPFRefDir = allOpts.IPF_reference_direction;

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

    millerDirs = Miller(num2cell(poleFigureDirections(1, :)), crystalSym);

    for i = 2:size(poleFigureDirections, 1)
        newMillerDir = Miller(num2cell(poleFigureDirections(i, :)), crystalSym);
        millerDirs = [millerDirs, newMillerDir];
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

    newMtexFigure('layout', [1, 1], 'visible', 'off');
    plotx2east;

    if useContours
        plotPDF(orientations, millerDirs, 'contourf');
        mtexColorbar;
    else
        ipfKey = ipfColorKey(crystalSym);
        ipfKey.inversePoleFigureDirection = vector3d.(upper(IPFRefDir));
        oriColors = ipfKey.orientation2color(orientations);
        plotPDF( ...
            orientations, ...
            millerDirs, ...
            'property', oriColors ...
        );
    end

    if ~isempty(allOpts.colourbar_limits)
        CLim(gcm, allOpts.colourbar_limits);
    end

    if allOpts.use_one_colourbar
        mtexColorbar % remove colorbars
        CLim(gcm, 'equal');
        mtexColorbar % add a single colorbar
    end

    aAxis = Miller(crystalSym.aAxis, 'xyz');
    bAxis = Miller(crystalSym.bAxis, 'xyz');
    cAxis = Miller(crystalSym.cAxis, 'xyz');

    xyzVecs = eye(3);
    xyzLabels = {'x', 'y', 'z'};
    aLabelAdded = 0;
    bLabelAdded = 0;
    cLabelAdded = 0;

    for i = 1:3

        if round(aAxis.xyz, 10) == xyzVecs(i, :)
            aLabelAdded = 1;
            xyzLabels(i) = append(xyzLabels(i), '/a');
        end

        if round(bAxis.xyz, 10) == xyzVecs(i, :)
            bLabelAdded = 1;
            xyzLabels(i) = append(xyzLabels(i), '/b');
        end

        if round(cAxis.xyz, 10) == xyzVecs(i, :)
            cLabelAdded = 1;
            xyzLabels(i) = append(xyzLabels(i), '/c');
        end

    end

    annotate( ...
        [xvector, yvector, zvector], ...
        'label', {xyzLabels{1}, xyzLabels{2}, xyzLabels{3}}, ...
        'backgroundcolor', 'w' ...
    )

    if ~aLabelAdded
        annotate([crystalSym.aAxis], 'label', {'a'}, 'backgroundcolor', 'w');
    end

    if ~bLabelAdded
        annotate([crystalSym.bAxis], 'label', {'b'}, 'backgroundcolor', 'w');
    end

    if ~cLabelAdded
        annotate([crystalSym.cAxis], 'label', {'c'}, 'backgroundcolor', 'w');
    end
    
    saveFigure('pole_figure.png');

    if plot_IPFKey
        newMtexFigure('layout', [1, 1], 'visible', 'off');
        plot(ipfKey);
        saveFigure('IPF_key.png');
    end

    close all;

    exitcode = 1;
end
