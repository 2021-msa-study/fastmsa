"""Command line script for FastMSA.

Test
"""
from __future__ import annotations

from pathlib import Path

import jinja2

from fastmsa.utils import cwd, scan_resource_dir
from pkg_resources import resource_string


class FastMsaCommand:
    def __init__(self, name: str, path: str = None):
        """Constructor.

        ``name`` should include only alpha-numeric chracters and underscore('_').
        """
        self.name = name.strip()
        self.path: Path
        assert self.name.isalnum()

        if not path:
            self.path = Path(".") / self.name
        else:
            self.path = Path(path)

    def init(self):
        """Initialize project.

        Steps:
            1. Copy ``templates/app``  to ``project_name``
            2. Rename ``templates/app`` to ``project_name/project_name``
        """

        with cwd(self.path):
            template_dir = "templates/app"
            res_names = scan_resource_dir(template_dir)

            for res_name in res_names:
                rel_path = res_name.replace(template_dir + "/", "")
                target_path = self.path / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                text = resource_string("fastmsa", res_name).decode()

                if target_path.name.endswith(".j2"):  # Jinja2 template
                    target_path = target_path.parent / target_path.name[:-3]
                    template = jinja2.Template(text)
                    text = template.render(msa=self)

                target_path.write_text(text)

            (self.path / "app").rename(self.name)
