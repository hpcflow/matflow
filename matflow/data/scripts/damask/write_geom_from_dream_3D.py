from damask import GeomGrid
import pathlib


def write_geom_from_dream_3D(dream_3D_hdf5_file_path: str) -> dict:
    """Write DAMASK geometry file from .dream3d file"""
    grid = GeomGrid.load_DREAM3D(dream_3D_hdf5_file_path, feature_IDs="FeatureIds")
    grid.save("geom.vti")
    geom_path = str(pathlib.Path().resolve() / "geom.vti")
    return {"geom_path": geom_path}
