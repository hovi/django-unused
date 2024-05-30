import os
from dataclasses import dataclass
from typing import List, Tuple, Optional

from django.apps import apps
from django.apps.config import AppConfig
from django.conf import settings


@dataclass
class TemplateInfo:
    file_path: str
    template_path: str
    app_config: Optional[AppConfig]


def find_app_templates() -> List[TemplateInfo]:
    templates: List[TemplateInfo] = []

    for config in apps.get_app_configs():
        config: AppConfig = config
        if str(config.path).find(str(settings.BASE_DIR)) > -1:
            dir_path = os.path.join(str(config.path), 'templates')
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    template_path = file_path.replace(dir_path, '').replace('\\', '/')[1:]
                    templates.append(TemplateInfo(
                        file_path=file_path,
                        template_path=template_path,
                        app_config=config,
                    ))

    return templates


def find_global_templates() -> List[TemplateInfo]:
    templates: List[TemplateInfo] = []

    if settings.TEMPLATES:
        for template_backend in settings.TEMPLATES:
            for dir in template_backend.get('DIRS', []):
                for root, dirs, files in os.walk(dir):
                    for file in files:
                        file_path = str(os.path.join(root, file))
                        template_path = file_path.replace(dir, '').replace('\\', '/')[1:]
                        templates.append(TemplateInfo(
                            file_path=file_path,
                            template_path=template_path,
                            app_config=None,
                        ))

    return templates


def find_py_files(exclude_dirs: List[str] = None) -> Tuple[List[str], List[str]]:
    if exclude_dirs is None:
        exclude_dirs = [os.path.join('example', 'server', 'tests')]

    pys: List[str] = []
    py_files: List[str] = []
    python_extensions = ['py']

    for config in apps.get_app_configs():
        if str(config.path).find(str(settings.BASE_DIR)) > -1:
            dir_path = str(config.path)
            for root, dirs, files in os.walk(dir_path):
                if any(exclude_dir in root for exclude_dir in exclude_dirs):
                    print(f'excluding: {root}')
                    continue
                for file in files:
                    filename, extension = os.path.splitext(file)
                    if extension[1:] in python_extensions:
                        py_file = os.path.join(root, file)
                        py_files.append(py_file)
                        pys.append(py_file.replace(dir_path, '')[1:])
    return py_files, pys
