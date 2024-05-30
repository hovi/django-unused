import unittest
from unittest.mock import MagicMock

from django_unused.management.commands._templates import (
    TemplateFilterOptions,
    filter_templates,
)
from django_unused.unused.find_templates import TemplateInfo


class TestFilterTemplates(unittest.TestCase):

    def setUp(self):
        self.app_config1 = MagicMock()
        self.app_config1.name = "app1"
        self.template1 = TemplateInfo(
            app_config=self.app_config1,
            template_path="dir1/template1.html",
            file_path="dir1/template1.html",
        )

        self.app_config2 = MagicMock()
        self.app_config2.name = "app2"
        self.template2 = TemplateInfo(
            app_config=self.app_config2,
            template_path="dir2/template2.html",
            file_path="dir2/template2.html",
        )

        self.template3 = TemplateInfo(
            app_config=None,
            template_path="dir3/template3.html",
            file_path="dir3/template3.html",
        )
        self.templates = [self.template1, self.template2, self.template3]

    def test_filter_templates_excluded_apps(self):
        filter_options = TemplateFilterOptions(excluded_apps=["app1"])

        filtered_templates = filter_templates(self.templates, filter_options)
        self.assertEqual(len(filtered_templates), 2)
        self.assertIn(self.template2, filtered_templates)
        self.assertIn(self.template3, filtered_templates)
        self.assertNotIn(self.template1, filtered_templates)

    def test_filter_templates_excluded_dirs(self):
        filter_options = TemplateFilterOptions(excluded_template_dirs=["dir2"])

        filtered_templates = filter_templates(self.templates, filter_options)
        self.assertEqual(len(filtered_templates), 2)
        self.assertIn(self.template1, filtered_templates)
        self.assertIn(self.template3, filtered_templates)
        self.assertNotIn(self.template2, filtered_templates)

    def test_filter_templates_excluded_apps_and_dirs(self):
        filter_options = TemplateFilterOptions(
            excluded_apps=["app1"], excluded_template_dirs=["dir2"]
        )

        filtered_templates = filter_templates(self.templates, filter_options)
        self.assertEqual(len(filtered_templates), 1)
        self.assertIn(self.template3, filtered_templates)
        self.assertNotIn(self.template1, filtered_templates)
        self.assertNotIn(self.template2, filtered_templates)


if __name__ == "__main__":
    unittest.main()
