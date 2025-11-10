# Configuration file for the Sphinx documentation builder -- Common config content
from __future__ import annotations
import copy
import importlib
import json
import re
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from ruamel.yaml import YAML
import tomlkit
from valida.datapath import DataPath, MapValue
from valida.schema import write_tree_html

from hpcflow.sdk.config.callbacks import callback_vars as config_callback_vars

if TYPE_CHECKING:
    from hpcflow.sdk.app import BaseApp
    from hpcflow.sdk.core.validation import Schema


def get_classmethods(cls: type) -> list[str]:
    """Get a list of class methods of a given class."""
    return sorted(
        k
        for k, v in cls.__dict__.items()
        if callable(getattr(cls, k))
        and not k.startswith("_")
        and isinstance(v, classmethod)
    )


def _write_valida_tree_html(
    schema: Schema,
    path: str | Path,
    from_path=None,
    anchor_root=None,
    heading_start_level=1,
    show_root_heading=True,
) -> Path:
    tree = schema.to_tree(nested=True, from_path=from_path)
    path_ = Path(path).resolve()
    with path_.open(mode="wt", encoding="utf-8") as fp:
        fp.write(
            write_tree_html(
                tree,
                anchor_root=anchor_root,
                heading_start_level=heading_start_level,
                show_root_heading=show_root_heading,
            )
        )
    return path_


_EXE_PLAT_LOOKUP = {
    "win.exe": "Windows executable",
    "macOS": "macOS executable",
    "linux": "Linux executable",
    "win-dir.zip": "Windows folder",
    "linux-dir.zip": "Linux folder",
    "macOS-dir.zip": "macOS folder",
}


def generate_download_links_table() -> str:
    """Generate install/index.rst file programmatically, including binary download links."""
    # Get just-released binaries:
    yaml = YAML()
    with Path("released_binaries.yml").open("rt") as fh:
        bins_dat: dict[str, str] = yaml.load(fh)

    return (
        '<table class="binary-downloads-table">'
        + "".join(
            f"""<tr><td>{
                _EXE_PLAT_LOOKUP["-".join(exe_name.split("-")[2:])]
            }</td><td><a href="{link}">{exe_name}</a></td></tr>"""
            for exe_name, link in sorted(bins_dat.items())
        )
        + "</table>"
    )


def expose_variables(app: BaseApp):
    """Expose some variables' reprs as string variables to be used in the docs.

    See: https://stackoverflow.com/a/69211912/5042280

    """

    app_name = app.name
    variables_to_export = ["app", "app_name"]
    frozen_locals = dict(locals())
    rst_epilog = "\n".join(
        map(lambda x: f".. |{x}| replace:: {frozen_locals[x]}", variables_to_export)
    )
    del frozen_locals
    return rst_epilog


def generate_config_file_validation_schema(app: BaseApp):
    all_cfg_schema = app.config._file.file_schema

    # merge built-in schema with custom schemas:
    config_schema = app.config.config_schemas
    for s_i in config_schema[1:]:
        config_schema[0].add_schema(s_i)

    # merge config file schema with config schemas:
    all_cfg_schema.add_schema(
        config_schema[0], root_path=DataPath("configs", MapValue(), "config")
    )

    # write default config file example:
    config = {"configs": {"default": copy.deepcopy(app.config._options.default_config)}}
    config["configs"]["default"]["config"]["machine"] = "HOSTNAME"
    log_file_path = config["configs"]["default"]["config"]["log_file_path"]
    config["configs"]["default"]["config"]["log_file_path"] = config_callback_vars(
        app.config, log_file_path
    )
    app.config._file._dump(config, Path("reference/_generated/default_config.yaml"))

    # write valida schema tree for config file:
    _write_valida_tree_html(
        all_cfg_schema,
        path="reference/_generated/config_validation.html",
        from_path=[MapValue("configs")],
        heading_start_level=2,
    )


def generate_parameter_validation_schemas(app: BaseApp):
    for param in app.parameters:
        schema = param._validation
        if schema:
            full_path = _write_valida_tree_html(
                schema=schema,
                path=f"reference/_generated/param_{param.typ}_validation.html",
                anchor_root=param.typ,
                show_root_heading=False,
                heading_start_level=2,
            )
            jinja_contexts["first_ctx"]["tree_files"][param.typ] = str(full_path)


def copy_all_demo_workflows(app: BaseApp):
    """Load WorkflowTemplate objects and copy template files from all builtin demo
    template files to the reference source directory (adjacent to the workflows.rst file
    within which they are included)."""
    return {
        name: {
            "obj": app.load_demo_workflow(name),
            "file_path": f"demo_workflow_{name}",
            "file_name": app.copy_demo_workflow(
                name, dst=Path(f"reference/demo_workflow_{name}"), doc=False
            ),
        }
        for name in app.list_demo_workflows()
    }


def prepare_API_reference_stub(app: BaseApp):
    contents = dedent(
        f"""\
        Python API
        ==========

        .. autosummary::
          :toctree: _autosummary
          :template: custom-module-template.rst
          :recursive:

          {app.module}
    """
    )
    with Path("reference/api.rst").open("wt") as fp:
        fp.write(contents)


def prepare_task_schema_action_info(app: BaseApp):
    """Write an HTML file for each task schema that lists the actions."""
    out: dict[str, dict[str, str]] = {}
    for ts_i in app.task_schemas:
        if not ts_i.web_doc:
            continue
        html = ts_i.get_info_html()
        rel_path = f"ts_{ts_i.name}_actions.html"
        dst = Path(f"reference/{rel_path}")
        with dst.open("wt", encoding="utf") as fh:
            fh.write(html)
        value = {
            "file_path": str(dst.resolve()),
            "file_name": dst.name,
        }

        out.setdefault(ts_i.objective.name, {})[
            ts_i.name if ts_i.method or ts_i.implementation else None
        ] = value

    return dict(sorted(out.items()))


with Path("config.jsonc").open("rt") as fp:
    jsonc_str = fp.read()
    # Strip out comments denoted by // to leave a valid JSON file
    json_str = re.sub(
        r'\/\/(?=([^"]*"[^"]*")*[^"]*$).*', "", jsonc_str, flags=re.MULTILINE
    )
    config_dat = json.loads(json_str)

app: BaseApp = importlib.import_module(config_dat["package"], "app")
release = app.version
project = config_dat["project"]
copyright = config_dat["copyright"]
author = config_dat["author"]
github_user = config_dat["github_user"]
github_repo = config_dat["github_repo"]
PyPI_project = config_dat["PyPI_project"]
switcher_JSON_URL = config_dat["switcher_JSON_URL"]
html_logo = config_dat["html_logo"]
additional_intersphinx = {
    k: tuple(v) for k, v in config_dat["additional_intersphinx"].items()
}

Path("./reference/_generated").mkdir(exist_ok=True)

# distribution name (i.e. name on PyPI):
with Path("../../pyproject.toml").open("rt") as fp:
    pyproj_data = tomlkit.load(fp)
    dist_name = pyproj_data["tool"]["poetry"]["name"]
    supported_python = pyproj_data["tool"]["poetry"]["dependencies"]["python"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.todo",
    "sphinx_jinja",
    "sphinx_copybutton",
    "sphinx_click",
    "sphinx_togglebutton",
    "sphinx_design",
    "myst_nb",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    **additional_intersphinx,
}

html_context = {
    "github_user": github_user,
    "github_repo": github_repo,
    "github_version": "develop",
    "doc_path": "docs/source",
}

jinja_contexts = {
    "first_ctx": {
        "app_name": app.name,
        "app_version": app.version,
        "app_description": app.description,
        "app_package_name": app.package_name,
        "app_module": app.module,
        "app_docs_import_conv": app.docs_import_conv,
        "dist_name": dist_name,
        "parameters": sorted(app.parameters),
        "task_schemas": app.task_schemas,
        "command_files": app.command_files,
        "environments": app.envs,
        "tree_files": {},
        "download_links_table_html": generate_download_links_table(),
        "github_user": github_user,
        "github_repo": github_repo,
        "supported_python": supported_python,
    }
}

jinja_globals = {
    "get_classmethods": get_classmethods,
    "parameter_task_schema_map": app.get_parameter_task_schema_map(),
    "demo_workflows": copy_all_demo_workflows(app),
    "task_schema_actions_html": prepare_task_schema_action_info(app),
}

# see: https://stackoverflow.com/a/62613202/5042280 for autosummary strategy
autosummary_generate = True
autodoc_typehints = "description"
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 4

templates_path = ["_templates"]
exclude_patterns = []

nb_execution_mode = "off"

text_newlines = "unix"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
html_js_files = ["js/custom.js"]
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "external_links": [],
    "switcher": {
        "json_url": switcher_JSON_URL,
        "version_match": release,
    },
    "navbar_end": ["theme-switcher", "navbar-icon-links", "version-switcher"],
    "use_edit_page_button": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": f"https://github.com/{github_user}/{github_repo}",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        },
        {
            "name": "PyPI",
            "url": f"https://pypi.org/project/{PyPI_project}",
            "icon": "fas fa-box",  # TODO: icon is smaller than in https://pydata-sphinx-theme.readthedocs.io/en/stable/index.html ?
        },
    ],
}

prepare_API_reference_stub(app)
rst_epilog = expose_variables(app)
generate_config_file_validation_schema(app)
generate_parameter_validation_schemas(app)
