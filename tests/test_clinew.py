from __future__ import print_function, absolute_import, division

from mw_uml_generator.gen.structure import create_project,up_project,create_aiohttp,gen_docker,gen_apijs

import os

import unittest

class CliTestCase(unittest.TestCase):
    def setUp(self):
        print(os.getcwd())
        # os.chdir('./tests')
        self.projectname ='cdcd'

    # def test_create_project(self):
    #     create_project(self.projectname,'aiohttp')
    #     assert os.path.exists(os.path.abspath(self.projectname))

    def test_up_project(self):
        os.chdir(self.projectname)
        # os.chdir('/work/tools/gen_flask')
        up_project()
        # up_project(False,'table')





