import importlib.util
import unittest
from pathlib import Path

class CatalogConversionTest(unittest.TestCase):
    def converter(self):
        script = Path(__file__).with_name('xcstrings_to_android.py')
        self.assertTrue(script.exists(), 'catalog converter has not been implemented')
        spec = importlib.util.spec_from_file_location('converter', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_collisions_have_stable_distinct_ids(self):
        mapping = self.converter().resource_ids(['Hello world', 'Hello-world', '123', '!!!'])
        self.assertEqual(len(set(mapping.values())), 4)
        self.assertTrue(all(__import__('re').fullmatch('[a-z][a-z0-9_]*', x) for x in mapping.values()))
        self.assertEqual(mapping, self.converter().resource_ids(['!!!', '123', 'Hello-world', 'Hello world']))

    def test_literal_percent_in_prose_stays_literal(self):
        self.assertEqual(self.converter().android_text('10% finished'), '10% finished')
        self.assertEqual(self.converter().android_text('20% slower'), '20% slower')

    def test_java_keywords_are_usable_resources(self):
        self.assertEqual(self.converter().resource_ids(['private'])['private'], 'text_private')

    def test_apple_formatters_become_android_formatters(self):
        self.assertEqual(self.converter().android_text('Week %lld: %@, %.1f%%'), 'Week %1$d: %2$s, %3$.1f%%')
        self.assertEqual(self.converter().android_text("Runner's \"A\" & <B>"), 'Runner\\\'s \\"A\\" & <B>')

if __name__ == '__main__': unittest.main()
