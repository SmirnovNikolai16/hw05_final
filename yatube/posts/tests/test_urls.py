from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Nikolai')
        cls.no_author = User.objects.create_user(username='Mark')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.author,
            group=cls.group
        )
        cls.templates_url_names = {
            '/': 'index.html',
            '/new/': 'new_post.html',
            '/group/test-slug/': 'group.html',
            f'/{cls.author}/': 'profile.html',
            f'/{cls.author}/{cls.post.id}/': 'post.html',
            f'/{cls.author}/{cls.post.id}/edit/': 'new_post.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.no_author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        for adress, template in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_redirects_unregistered_user(self):
        """
        Доступность URL гостевому пользователю и проверка редиректа
        недоступных страниц.
        """
        for adress in self.templates_url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                if response.status_code == 302:
                    self.assertRedirects(
                        response, f'/auth/login/?next={adress}'
                    )
                else:
                    self.assertEqual(response.status_code, 200)

    def test_url_for_authorized_user(self):
        """Доступность URL авторизованному пользователю - автору поста."""
        for adress in self.templates_url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_url_edit_page_authorized_user_not_author_post(self):
        """Доступность URL авторизованному пользователю - НЕ автору поста."""
        for adress in self.templates_url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client2.get(adress)
                if response.status_code != 200:
                    self.assertEqual(response.status_code, 302)
                    self.assertRedirects(
                        response,
                        reverse('post', args=[self.author, self.post.id])
                    )

    def test_page_not_found(self):
        """Проверка возвращает ли URL код 404, если страница не найдена"""
        response = self.guest_client.get('404/')
        self.assertEqual(response.status_code, 404)
