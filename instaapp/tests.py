import io
import json
import zipfile
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class UploadZipTests(TestCase):
    def _build_zip(self, names_and_payloads):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            for name, payload in names_and_payloads:
                if isinstance(payload, str):
                    data = payload.encode('utf-8')
                else:
                    data = json.dumps(payload).encode('utf-8')
                archive.writestr(name, data)
        buffer.seek(0)
        return buffer

    def test_accepts_json_files_in_zip(self):
        followers_payload = [
            {
                'string_list_data': [
                    {'value': 'alice', 'href': 'https://www.instagram.com/alice/'},
                    {'value': 'bob', 'href': 'https://www.instagram.com/bob/'},
                ]
            }
        ]
        following_payload = {
            'relationships_following': [
                {
                    'title': 'alice',
                    'string_list_data': [{'href': 'https://www.instagram.com/alice/'}],
                },
                {
                    'title': 'carol',
                    'string_list_data': [{'href': 'https://www.instagram.com/carol/'}],
                },
            ]
        }
        zip_buffer = self._build_zip([
            ('followers_1.json', followers_payload),
            ('following.json', following_payload),
        ])
        uploaded = SimpleUploadedFile(
            'instagram_export.zip',
            zip_buffer.getvalue(),
            content_type='application/zip',
        )

        response = self.client.post(reverse('upload'), {'zip_file': uploaded})

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Total Followers', content)
        self.assertIn('Analysis Results', content)

    def test_accepts_json_files_in_zip_api(self):
        followers_payload = [
            {
                'string_list_data': [
                    {'value': 'alice', 'href': 'https://www.instagram.com/alice/'},
                ]
            }
        ]
        following_payload = {
            'relationships_following': [
                {
                    'title': 'carol',
                    'string_list_data': [{'href': 'https://www.instagram.com/carol/'}],
                },
            ]
        }
        zip_buffer = self._build_zip([
            ('followers_1.json', followers_payload),
            ('following.json', following_payload),
        ])
        uploaded = SimpleUploadedFile('instagram_export.zip', zip_buffer.getvalue(), content_type='application/zip')
        response = self.client.post(reverse('upload'), {'zip_file': uploaded}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['non_follower_count'], 1)

    def test_rejects_html_files_in_zip(self):
        zip_buffer = self._build_zip([
            ('followers.html', '<html><body>followers</body></html>'),
            ('following.html', '<html><body>following</body></html>'),
        ])
        uploaded = SimpleUploadedFile(
            'instagram_export.zip',
            zip_buffer.getvalue(),
            content_type='application/zip',
        )

        response = self.client.post(reverse('upload'), {'zip_file': uploaded})

        self.assertEqual(response.status_code, 400)
        self.assertIn('HTML files are not supported', response.content.decode('utf-8'))


class StaticAssetsTests(TestCase):
    def test_serves_styles_css(self):
        response = self.client.get('/asset/css/styles.css')
        self.assertEqual(response.status_code, 200)

    def test_home_page_serves_index_without_js_files(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertNotIn('navbar.js', content)
        self.assertNotIn('app.js', content)

