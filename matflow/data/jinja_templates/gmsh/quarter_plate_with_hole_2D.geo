SetFactory("OpenCASCADE");
General.Terminal = 1;

Geometry.PointLabels = 1;
Geometry.CurveLabels = 1;
Geometry.SurfaceLabels = 1;
Geometry.VolumeLabels = 0;

// Geometric variables
plate_width = {{ plate_width }};
plate_diff = {{ plate_diff }}; // Must be positive
plate_height = plate_width+plate_diff;
hole_rad = {{ hole_diameter }}/2;

hole_loc_x = 0.0;
hole_loc_y = 0.0;
hole_circ = 2*Pi*hole_rad;

// Mesh variables
elem_order = 1;

hole_sect_nodes = {{ hole_sect_nodes }}; // Must be odd
plate_rad_nodes = {{ plate_radial_nodes }};
plate_diff_nodes = {{ plate_diff_nodes }}; // numbers of nodes along the rectangular extension
plate_edge_nodes = Floor((hole_sect_nodes-1)/2)+1;
elem_size = hole_circ/(4*(hole_sect_nodes-1));
tol = elem_size; // Used for bounding box selection tolerance


// ============================
// Points (corners of the quadrilateral)
Point(1) = {0, 0, 0, 0.1};
Point(2) = {plate_width/2, 0, 0, 0.1};
Point(3) = {plate_width/2, plate_width/2, 0, 0.1};
Point(4) = {Cos(Pi / 4)*hole_rad, Cos(Pi / 4)*hole_rad, 0, 0.1};

// ============================
// Lines (edges of quadrilateral)
Line(1) = {1, 2};  // bottom
Line(2) = {2, 3};  // right
Line(3) = {3, 4};  // top
Line(4) = {4, 1};  // left

// ============================
// Line loop and surface
Line Loop(10) = {1, 2, 3, 4};
s1 = news;
Plane Surface(s1) = {10};

// ============================
// Points (corners of the quadrilateral)
Point(5) = {0, 0, 0, 0.1};
Point(6) = {0, plate_width/2, 0, 0.1};
Point(7) = {plate_width/2, plate_width/2, 0, 0.1};
Point(8) = {Cos(Pi / 4)*hole_rad, Cos(Pi / 4)*hole_rad, 0, 0.1};

// ============================
// Lines (edges of quadrilateral)
Line(5) = {5, 6};  // bottom
Line(6) = {6, 7};  // right
Line(7) = {7, 8};  // top
Line(8) = {8, 5};  // left

// ============================
// Line loop and surface
Line Loop(30) = {5, 6, 7, 8};
s2 = news;
Plane Surface(s2) = {30};


Point(9) = {0, plate_width/2, 0, 0.1};
Point(10) = {plate_width/2, plate_width/2, 0, 0.1};
Point(11) = {plate_width/2, plate_height/2, 0, 0.1};
Point(12) = {0, plate_height/2, 0, 0.1};

Line(9) = {9, 10}; 
Line(10) = {10, 11};  
Line(11) = {11, 12};  
Line(12) = {12, 9}; 


// Line loop and surface
Line Loop(50) = {9, 10, 11, 12};
s3 = news;
Plane Surface(s3) = {50};


// Create circular hole
c1 = newc; Circle(c1) = {0.0, 0.0, 0.0, hole_rad};
cl1 = newcl; Curve Loop(cl1) = {c1};
s_hole = news; Plane Surface(s_hole) = {cl1};

// Cut the hole from the local surfaces
BooleanDifference{ Surface{s1, s2, s3}; Delete; }{ Surface{s_hole}; Delete; }


// Define a physical point to fix z in the corner (prevent rotation/translation)
// Point(1000) = {hole_rad, 0.0, 0.0, 0.1};
// Physical Point("hole-node") = {1000};

// Point(1001) = {hole_rad + 1e-6, 0, 0, 0.1};
// Line(9999) = {1000, 1001};
// Physical Line("hole-node-line") = {9999};

// Circle(9000) = {hole_rad, 0.0, 0.0, hole_rad/4};
// Physical Surface("hole-surface") = {9000};

// ============================
// Transfinite meshing
Transfinite Line {1, 3, 5, 6, 9} = plate_edge_nodes;
Transfinite Line {2, 4, 7} = plate_rad_nodes; 
Transfinite Line {8, 10} = plate_diff_nodes;

Transfinite Surface {s1};
Recombine Surface {s1}; 

Transfinite Surface {s2};
Recombine Surface {s2}; 

Transfinite Surface {s3};
Recombine Surface {s3};

// Extrude{0.0,0.0,plate_thick}{
//     Surface{:}; Layers{plate_thick_layers}; Recombine;
// }

//------------------------------------------------------------------------------
// Physical lines and surfaces for export/BCs

Physical Surface("plate") = {Surface{:}};

Physical Curve("y-mid-line") = {Curve In BoundingBox{
    0.0-tol,0.0-tol,0.0-tol,
    plate_width/2+tol,0.0+tol,0.0+tol}};

Physical Curve("y-top-line") = {Curve In BoundingBox{
    0.0-tol,plate_height/2-tol,0.0-tol,
    plate_width/2+tol,plate_height/2+tol,0.0+tol}};

Physical Curve("x-mid-line") = {Curve In BoundingBox{
    0.0-tol,0.0-tol,0.0-tol,
    0.0+tol,plate_height/2+tol,0.0+tol}};

// ============================
num_threads = 4;

Mesh.Algorithm = 6;
Mesh.Algorithm3D = 10;

General.NumThreads = num_threads;
Mesh.MaxNumThreads1D = num_threads;
Mesh.MaxNumThreads2D = num_threads;
Mesh.MaxNumThreads3D = num_threads;

Mesh.ElementOrder = elem_order;
Mesh 2;
