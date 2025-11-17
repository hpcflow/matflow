from PyInstaller.utils.hooks import collect_data_files

hiddenimports = [
    "matflow.data.data_manifests",
    "matflow.data.scripts",
    "matflow.data.jinja_templates",
    "matflow.data.template_components",
    "matflow.data.workflows",
    "matflow.param_classes",
    "matflow.tests.data",
]

py_include_kwargs = dict(include_py_files=True, excludes=("**/__pycache__",))
datas = (
    collect_data_files("matflow.data.data_manifests")
    + collect_data_files("matflow.data.scripts", **py_include_kwargs)
    + collect_data_files("matflow.data.jinja_templates", **py_include_kwargs)
    + collect_data_files("matflow.data.template_components")
    + collect_data_files("matflow.data.workflows")
    + collect_data_files("matflow.tests", **py_include_kwargs)
    + collect_data_files("matflow.tests.data")
)
