function load_texture_component(inputs_JSON_path, outputs_HDF5_path, outputs_JSON_path)

    rng(str2double(getenv('MATFLOW_RUN_RANDOM_SEED')));

    all_args = jsondecode(fileread(inputs_JSON_path));

    num_grains = all_args.num_grains;
    num_components = all_args.num_components;
    odf_fname = all_args.odf_fname;
    index = all_args.index;
    filename = all_args.filename

    CS = crystalSymmetry('cubic');

    components = equispacedSO3Grid(CS, 'points', num_components);

    n_halfwidths = length(components)

    data = table2array(readtable(filename));

    halfwidths = data(index,1:n_halfwidths);
    weights = data(index,n_halfwidths+1:end);

    odf = weights(:,end) * uniformODF(CS);
    
    for n = 1:n_halfwidths;
    
        if halfwidths(n) ~= 0;
    
            odf = odf + weights(n) * unimodalODF(components(n),CS,'halfwidth',halfwidths(n)*degree);
        end
    end

    % Optional: sample the ODF and reconstruct with calcDensity
    % ori = odf.discreteSample(100000);
    % odf = calcDensity(ori);

    % ODF representation option 1: SO3FunHarmonic
    % odf = SO3FunHarmonic(odf, 'bandwidth', 16);

    % ODF representation option 2: SO3FunRBF
    odf = SO3FunRBF(odf);

    rng("shuffle");
    orientations = odf.discreteSample(num_grains);
    export_orientations_HDF5(orientations, halfwidths, weights, outputs_HDF5_path, outputs_JSON_path);

    save(odf_fname, 'odf');

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

function export_orientations_HDF5(orientations, halfwidth, weights, hdf5_fileName, JSON_fileName)
    alignment = prepare_crystal_alignment(orientations.CS);
    ori_data = [orientations.a, orientations.b, orientations.c, orientations.d];

    % TODO: why?
    ori_data(:, 2:end) = ori_data(:, 2:end) * -1;

    ori_data = ori_data';
    h5create(hdf5_fileName, '/orientations/data', size(ori_data));
    h5write(hdf5_fileName, '/orientations/data', ori_data);
    h5writeatt(hdf5_fileName, '/orientations', 'representation_type', 0);
    h5writeatt(hdf5_fileName, '/orientations', 'representation_quat_order', 0);
    h5writeatt(hdf5_fileName, '/orientations', 'unit_cell_alignment', alignment);
    % h5create(fileName, '/odf_parameters/halfwidths', size(halfwidth));
    % h5write(fileName, '/odf_parameters/halfwidths', halfwidth);
    % h5create(fileName, '/odf_parameters/weights', size(weights));
    % h5write(fileName, '/odf_parameters/weights', weights);
    odf_parameters.halfwidths = halfwidth;
    odf_parameters.weights = weights;
    s = struct('odf_parameters', odf_parameters);
    json_str = jsonencode(s);
    fid = fopen(strrep(JSON_fileName, '.hdf5', '_odf_parameters.json'), 'w');
    fprintf(fid, json_str);
    fclose(fid);
end

function [x,v] = randfixedsum(n,m,s,a,b)

    if (m~=round(m))|(n~=round(n))|(m<0)|(n<1)
        error('n must be a whole number and m a non-negative integer.')
    elseif (s<n*a)|(s>n*b)|(a>=b)
        error('Inequalities n*a <= s <= n*b and a < b must hold.')
    end

    s = (s-n*a)/(b-a);

    k = max(min(floor(s),n-1),0);
    s = max(min(s,k+1),k);
    s1 = s - [k:-1:k-n+1];
    s2 = [k+n:-1:k+1] - s;
    w = zeros(n,n+1); w(1,2) = realmax;
    t = zeros(n-1,n);
    tiny = 2^(-1074);
    for i = 2:n
        tmp1 = w(i-1,2:i+1).*s1(1:i)/i;
        tmp2 = w(i-1,1:i).*s2(n-i+1:n)/i;
        w(i,2:i+1) = tmp1 + tmp2;
        tmp3 = w(i,2:i+1) + tiny;
        tmp4 = (s2(n-i+1:n) > s1(1:i));
        t(i-1,1:i) = (tmp2./tmp3).*tmp4 + (1-tmp1./tmp3).*(~tmp4);
    end

    v = n^(3/2)*(w(n,k+2)/realmax)*(b-a)^(n-1);

    x = zeros(n,m);
    if m == 0, return, end
    rt = rand(n-1,m);
    rs = rand(n-1,m);
    s = repmat(s,1,m);
    j = repmat(k+1,1,m);
    sm = zeros(1,m); pr = ones(1,m);
    for i = n-1:-1:1
        e = (rt(n-i,:)<=t(i,j));
        sx = rs(n-i,:).^(1/i);
        sm = sm + (1-sx).*pr.*s/(i+1);
        pr = sx.*pr;
        x(n-i,:) = sm + pr.*e;
        s = s - e; j = j - e;
    end
    x(n,:) = sm + pr.*s;

    rp = rand(n,m);
    [ig,p] = sort(rp);
    x = (b-a)*x(p+repmat([0:n:n*(m-1)],n,1))+a;

end
