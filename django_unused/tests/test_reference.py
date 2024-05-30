import unittest
from django_unused.management.commands._templates import determine_reference_type


class TestDetermineReferenceType(unittest.TestCase):

    def test_include_reference(self):
        self.assertEqual(
            determine_reference_type("{% include 'some_template.html' %}"), "include"
        )
        self.assertEqual(
            determine_reference_type(
                "Some text before {% include 'partials/header.html' %} some text after"
            ),
            "include",
        )
        self.assertEqual(
            determine_reference_type(
                "{% include 'footer.html' %} and some trailing text"
            ),
            "include",
        )

    def test_extend_reference(self):
        self.assertEqual(
            determine_reference_type("{% extends 'base.html' %}"), "extend"
        )
        self.assertEqual(
            determine_reference_type(
                "Text before {% extends 'layouts/main.html' %} text after"
            ),
            "extend",
        )
        self.assertEqual(
            determine_reference_type(
                "{% extends 'templates/master.html' %} trailing text"
            ),
            "extend",
        )

    def test_unknown_reference(self):
        self.assertEqual(determine_reference_type("{% block content %}"), "unknown")
        self.assertEqual(determine_reference_type("{% load custom_tags %}"), "unknown")
        self.assertEqual(
            determine_reference_type("{% comment 'this is a comment' %}"), "unknown"
        )
        self.assertEqual(
            determine_reference_type("This is just a plain line."), "unknown"
        )

    def test_whitespace_handling(self):
        self.assertEqual(
            determine_reference_type("  {% include 'some_template.html' %}  "),
            "include",
        )
        self.assertEqual(
            determine_reference_type("\t{% extends 'base.html' %}\t"), "extend"
        )
        self.assertEqual(
            determine_reference_type("\n{% include 'footer.html' %}\n"), "include"
        )

    def test_partial_template_tag(self):
        self.assertEqual(determine_reference_type("{% include"), "unknown")
        self.assertEqual(determine_reference_type("{% extends"), "unknown")
        self.assertEqual(
            determine_reference_type("{% include 'some_template.html'"), "unknown"
        )
        self.assertEqual(determine_reference_type("{% extends 'base.html'"), "unknown")


if __name__ == "__main__":
    unittest.main()
