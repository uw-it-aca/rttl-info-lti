# Copyright 2026 UWIT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.test import SimpleTestCase

from rttlinfo.dataclasses import CourseConfiguration, GitpullerTarget
from rttlinfo.forms import CourseConfigurationForm

IMAGE_BASE = 'us-west1-docker.pkg.dev/uwit-mci-axdd/rttl-images/'


def make_form(**overrides):
    data = {
        'cpu_request': '2',
        'memory_request': '4',
        'storage_request': '5',
        'container_image': 'scipy',
    }
    data.update(overrides)
    return CourseConfigurationForm(data)


class CourseConfigurationFormTest(SimpleTestCase):
    def test_custom_image_requires_url_and_defaults_tag(self):
        form = make_form(container_image='custom')
        self.assertFalse(form.is_valid())
        self.assertIn('Image URL is required', str(form.non_field_errors()))

        form = make_form(container_image='custom', custom_image_url='u/i')
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['custom_image_tag'], 'latest')

    def test_invalid_choice_rejected(self):
        self.assertFalse(make_form(cpu_request='64').is_valid())

    def test_hub_admins_list_strips_domains_and_blanks(self):
        form = make_form(additional_admins=' a@uw.edu, b ,, ')
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_hub_admins_list(), ['a', 'b'])

    def test_hub_admins_list_empty(self):
        form = make_form()
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.get_hub_admins_list())

    def test_features_list(self):
        form = make_form(feature_nfs='on', feature_binderhub='on')
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_features_list(), ['nfs', 'binderhub'])

    def test_to_dataclass_requires_valid_form(self):
        with self.assertRaises(ValueError):
            make_form(cpu_request='64').to_dataclass()

    def test_to_dataclass_predefined_image(self):
        form = make_form(
            container_image='r', feature_nfs='on',
            gitpuller_uri='https://github.com/o/r.git',
            gitpuller_tag='main', gitpuller_sync_dir='mats',
            configuration_comments='c')
        config = form.to_dataclass()
        self.assertEqual(config.image_uri, IMAGE_BASE + 'jupyter-r-notebook')
        self.assertEqual(
            (config.cpu_request, config.memory_request,
             config.storage_request), (2, 4, 5))
        self.assertEqual(config.features_request, 'nfs')
        self.assertEqual(
            config.gitpuller_targets,
            [GitpullerTarget('https://github.com/o/r.git', 'main', 'mats')])
        self.assertEqual(config.configuration_comments, 'c')

    def test_to_dataclass_custom_image(self):
        config = make_form(
            container_image='custom', custom_image_url='reg/img',
            custom_image_tag='v2').to_dataclass()
        self.assertEqual((config.image_uri, config.image_tag),
                         ('reg/img', 'v2'))
        self.assertEqual(config.gitpuller_targets, [])

    def test_from_dataclass_known_image(self):
        form = CourseConfigurationForm()
        form.from_dataclass(CourseConfiguration(
            cpu_request=4, memory_request=8, storage_request=10,
            image_uri=IMAGE_BASE + 'jupyter-rstudio-notebook',
            features_request='NFS, binderhub',
            gitpuller_targets=[GitpullerTarget('u', 't', 'd')]))
        self.assertEqual(form.initial['container_image'], 'rstudio')
        self.assertEqual(form.initial['cpu_request'], '4')
        self.assertTrue(form.initial['feature_nfs'])
        self.assertTrue(form.initial['feature_binderhub'])
        self.assertEqual(form.initial['gitpuller_uri'], 'u')
        self.assertNotIn('custom_image_url', form.initial)

    def test_from_dataclass_unknown_image_is_custom(self):
        form = CourseConfigurationForm()
        form.from_dataclass(CourseConfiguration(
            cpu_request=1, memory_request=2, storage_request=5,
            image_uri='other/img', image_tag='t'))
        self.assertEqual(form.initial['container_image'], 'custom')
        self.assertEqual(form.initial['custom_image_url'], 'other/img')
        self.assertEqual(form.initial['custom_image_tag'], 't')

    def test_set_hub_admins(self):
        form = CourseConfigurationForm()
        form.set_hub_admins(['a', 'b'])
        self.assertEqual(form.initial['additional_admins'], 'a, b')
        form.set_hub_admins(None)
        self.assertEqual(form.initial['additional_admins'], '')
