import sys
import time
import unittest
from pathlib import Path

try:
    from platformio.public import TestCase, TestRunnerBase, TestStatus
except ImportError:
    TestCase = TestStatus = None
    TestRunnerBase = object


class CustomTestRunner(TestRunnerBase):
    def stage_building(self):
        pass

    def stage_uploading(self):
        pass

    def stage_testing(self):
        carpeta = Path(__file__).resolve().parent
        sys.path.insert(0, str(carpeta))
        suite = unittest.defaultTestLoader.discover(str(carpeta), pattern="test_simulacion.py")
        runner = self

        class Resultado(unittest.TestResult):
            def startTest(self, test):
                super().startTest(test)
                self.inicio = time.time()

            def agregar(self, test, estado, mensaje=None):
                runner.test_suite.add_case(TestCase(
                    name=test._testMethodName, status=estado, message=mensaje,
                    duration=time.time() - self.inicio))

            def addSuccess(self, test):
                self.agregar(test, TestStatus.PASSED)

            def addFailure(self, test, err):
                self.agregar(test, TestStatus.FAILED, self._exc_info_to_string(err, test))

            def addError(self, test, err):
                self.agregar(test, TestStatus.ERRORED, self._exc_info_to_string(err, test))

            def addSkip(self, test, reason):
                self.agregar(test, TestStatus.SKIPPED, reason)

        suite.run(Resultado())
