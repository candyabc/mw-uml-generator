from mw_uml_generator.gen.structure import gen_apijs

import os

import unittest


class CliTestCase(unittest.TestCase):
    def setUp(self):
        pass

    # def test_create_project(self):
    #     create_project(project_name=self.projectname)
    #     assert os.path.exists(self.projectname)

    def test_swagger2api(self):
        gen_apijs(None,'./mw-maintenance.yml','./test.js')

        gen_apijs('maintence',None,None)



