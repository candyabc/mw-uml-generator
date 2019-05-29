from __future__ import print_function, absolute_import, division
from mw_uml_generator.gen.structure import create_project,up_project,create_aiohttp,gen_docker,gen_apijs

import os

import unittest

class CliTestCase(unittest.TestCase):
    def setUp(self):
        # print(os.getcwd())
        # os.chdir('./tests')
        self.projectname ='mw-apppush-srv'

    # def test_create_project(self):
    #     create_project(project_name=self.projectname)
    #     assert os.path.exists(self.projectname)

    def test_up_project(self):
        os.chdir('D:\\work\\mwwork\\mw-notice\\mw-apppush-srv')
        up_project()





