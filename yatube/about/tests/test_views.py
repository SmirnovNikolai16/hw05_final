from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.templates_page_names = {
            'about:author': 'author.html',
            'about:tech': 'tech.html'
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени static_pages:about, доступен."""
        for adress in self.templates_page_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(reverse(adress))
                self.assertEqual(response.status_code, 200)

    def test_about_pages_uses_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
        for adress, template in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse(adress))
                self.assertTemplateUsed(response, template)
