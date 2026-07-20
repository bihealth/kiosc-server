"""Tests for Ajax API views in the containers app"""

from django.urls import reverse


class TestPluginSearchResultsAjaxView(TestSearchMixin, ProjectPermissionTestBase):
    """Tests for PluginSearchResultsAjaxView view with containers and logs"""

    def setUp(self):
        super().setUp()
        self.other_project = self.make_project(
            'other_project',
            PROJECT_TYPE_PROJECT,
            self.category,
            description='description',
        )
        self.container = ContainerFactory(project=self.project)
        self.other_container = ContainerFactory(project=self.other_project)
        self.logs = ContainerLogEntryFactory(container=self.container)
        self.other_logs = ContainerLogEntryFactory(container=self.other_container)
        # Promote user to guest
        self.make_assignment(
            self.other_project, self.user_finder_cat, self.role_guest
        )

    def test_search_source(self):
        """Test simple search with source"""
        containers, logs = self._get_search_results(
            {
                'terms': f'["container 0"]',
                'keywords': '{}',
            },
        )
        self.assertEqual(len(containers), 1)
        self.assertEqual(self.container.title in containers[0][0]['value'])

    def test_search_source_type_source(self):
        """Test simple search with source and source type"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_search'),
                {
                    'plugin': 'samplesheets',
                    'terms': f'["{self.source.name}"]',
                    'keywords': '{"type": "source"}',
                },
            )
        rows = self._get_rows(response)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0]['value'], self.source.name)

    def test_search_source_type_sample(self):
        """Test simple search with source and sample type (should fail)"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_search'),
                {
                    'plugin': 'samplesheets',
                    'terms': f'["{self.source.name}"]',
                    'keywords': '{"type": "sample"}',
                },
            )
        rows = self._get_rows(response)
        self.assertEqual(len(rows), 0)

    def test_search_sample(self):
        """Test simple search with sample"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_search'),
                {
                    'plugin': 'samplesheets',
                    'terms': f'["{self.sample.name}"]',
                    'keywords': '{}',
                },
            )
        rows = self._get_rows(response)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0]['value'], self.sample.name)

    def test_search_sample_type_sample(self):
        """Test simple search with sample and sample type"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_search'),
                {
                    'plugin': 'samplesheets',
                    'terms': f'["{self.sample.name}"]',
                    'keywords': '{"type": "sample"}',
                },
            )
        rows = self._get_rows(response)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0]['value'], self.sample.name)

    def test_search_sample_type_source(self):
        """Test simple search with sample and source type (should fail)"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_search'),
                {
                    'plugin': 'samplesheets',
                    'terms': f'["{self.sample.name}"]',
                    'keywords': '{"type": "source"}',
                },
            )
        rows = self._get_rows(response)
        self.assertEqual(len(rows), 0)

    def test_search_multi(self):
        """Test simple search with multiple terms"""
        with self.login(self.user):
            response = self.client.post(
                reverse('projectroles:ajax_search'),
                {
                    'plugin': 'samplesheets',
                    'terms': f'["{self.source.name}", "{self.sample.name}"]',
                    'keywords': '{}',
                },
            )
        rows = self._get_rows(response)
        self.assertEqual(len(rows), 2)

    # =================
    def test_search_term_with_type(self):
        """Test permissions for search view limited by type."""
        data = {'s': 'container type:containerbackgroundjob'}

        # Superuser sees everything
        results = self._get_search_results(self.superuser, data)
        self.assertEqual(
            set(results['all'].items), set([self.bg_job, self.other_bg_job])
        )

        # Good users see only the container in their project
        for user in self.good_users:
            results = self._get_search_results(user, data)
            self.assertEqual(results['all'].items, [self.bg_job])

        # Bad users should not see any results
        for user in self.bad_users:
            results = self._get_search_results(user, data)
            self.assertEqual(results['all'].items, [])

        # Special users
        results = self._get_search_results(self.user_contributor_cat, data)
        self.assertEqual(
            set(results['all'].items), set([self.bg_job, self.other_bg_job])
        )
        results = self._get_search_results(self.user_finder_cat, data)
        self.assertEqual(results['all'].items, [self.other_bg_job])

        # Anonymous
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 302)

    def test_search_term_with_type_and_keyword(self):
        """Test permissions for search view limited by type and project."""
        data = {
            's': (
                'description '
                'type:containerbackgroundjob '
                f'project:{self.project.sodar_uuid}'
            )
        }

        # Superuser sees everything
        results = self._get_search_results(self.superuser, data)
        self.assertEqual(set(results['all'].items), set([self.bg_job]))

        # Good users see only the container in their project
        for user in self.good_users:
            results = self._get_search_results(user, data)
            self.assertEqual(results['all'].items, [self.bg_job])

        # Bad users should not see any results
        for user in self.bad_users:
            results = self._get_search_results(user, data)
            self.assertEqual(results['all'].items, [])

        # Special users
        results = self._get_search_results(self.user_contributor_cat, data)
        self.assertEqual(set(results['all'].items), set([self.bg_job]))
        results = self._get_search_results(self.user_finder_cat, data)
        self.assertEqual(results['all'].items, [])

        # Anonymous
        res = self.client.get(self.url, data)
        self.assertEqual(res.status_code, 302)
