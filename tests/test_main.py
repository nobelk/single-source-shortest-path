import unittest
from unittest.mock import patch
import sys
from io import StringIO


class TestMain(unittest.TestCase):

    def test_main_function(self):
        """Test the main function"""
        # Import here to avoid issues with module loading
        from sssp.main import main

        # Test that main function runs without error
        # Since it just passes, this should complete successfully
        result = main()
        self.assertIsNone(result)  # main() returns None

    def test_main_module_execution(self):
        """Test running the module as main"""
        # Test the if __name__ == "__main__" block
        # We need to simulate the module being run as main
        import importlib.util
        import sys
        import os

        # Get the path to the main.py file
        main_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "sssp", "main.py"
        )
        main_path = os.path.abspath(main_path)

        # Create a module spec and execute it as __main__
        spec = importlib.util.spec_from_file_location("__main__", main_path)
        main_module = importlib.util.module_from_spec(spec)

        # Temporarily set __name__ to __main__ to trigger the if block
        old_name = getattr(main_module, "__name__", None)
        main_module.__name__ = "__main__"

        try:
            spec.loader.exec_module(main_module)
            # If we reach here, the module executed successfully
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Main module execution failed: {e}")
        finally:
            # Restore original name if it existed
            if old_name is not None:
                main_module.__name__ = old_name


if __name__ == "__main__":
    unittest.main()
