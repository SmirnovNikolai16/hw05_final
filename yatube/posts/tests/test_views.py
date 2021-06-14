import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='Mark')
        cls.user2 = User.objects.create_user(username='Nikolai')
        cls.user3 = User.objects.create_user(username='Maks')
        cls.group = Group.objects.create(title='reader',
                                         slug='test',
                                         description='Тест')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        cls.data_fields = {
            'user': cls.user2,
            'author': cls.user
        }

        cls.templates_url_names = {
            reverse('index'): 'index.html',
            reverse('new_post'): 'new_post.html',
            reverse('group_posts', kwargs={'slug': 'test'}): 'group.html',
            reverse('profile', args=[cls.user]): 'profile.html',
            reverse('post', args=[cls.user, cls.post.id]): 'post.html',
            reverse('post_edit', args=[cls.user, cls.post.id]): 'new_post.html'
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client3 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)
        self.authorized_client3.force_login(self.user3)

    def context_checks(self, response, context):
        first_object = response.context[context][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Текст поста')
        self.assertEqual(post_author_0, 'Mark')
        self.assertEqual(post_group_0, 'reader')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_pages_use_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
        cache.clear()
        for adress, template in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """
        Шаблон index сформирован с правильным контекстом.
        При создании поста с указанием группы,
        этот пост появляется на главной странице сайта.
        """
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        self.context_checks(response, 'page')

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test'})
        )
        first_object = response.context['group']
        second_objects = response.context['page'][0]
        self.assertEqual(first_object.title, 'reader')
        self.assertEqual(first_object.description, 'Тест')
        self.assertEqual(first_object.slug, 'test')
        self.assertEqual(second_objects.image, 'posts/small.gif')

    def test_index_show_correct_context_no_group(self):
        """
        Шаблон index сформирован с правильным контекстом
        без указания группы.
        """
        cache.clear()
        response = self.client.get(reverse('index'))
        first_object = response.context['page'][0]
        post_group = first_object.group
        if post_group is None:
            self.assertIsNone(post_group, None)
        else:
            self.assertEqual(post_group.title, 'reader')

    def test_new_post_pages_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_pages_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post_edit',
                    args=[self.user, self.post.id])
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('profile', args=[self.user])
        )
        self.context_checks(response, 'page')

    def test_separate_post_pages_show_correct_context(self):
        """
        Шаблон страницы отдельного поста
        сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('post', args=[self.user, self.post.id])
        )
        fields = {'post_count': self.user.posts.count(),
                  'author': self.post.author,
                  'post': self.post}
        for value, expected in fields.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)
        self.assertEqual(response.context['post'].image, 'posts/small.gif')

    def test_verification_of_subscriptions(self):
        """Авторизованный пользователь может подписываться на
        авторов поста и удалять их из подписок.
        """
        followings = Follow.objects.all()
        self.assertEqual(followings.count(), 0)
        self.authorized_client2.post(
            reverse('profile_follow', args=[self.user]),
            data=self.data_fields
        )
        self.assertEqual(
            followings.count(), 1,
            "Авторизованный пользователь не подписан ни на одного автора"
        )
        self.authorized_client2.post(
            reverse('profile_unfollow', args=[self.user]),
            data=self.data_fields
        )
        self.assertEqual(
            followings.count(), 0,
            "Авторизованный пользователь не удалил автора из подписок"
        )

    def test_post_display_for_subscribers(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан на него
        """
        self.authorized_client2.post(
            reverse('profile_follow', args=[self.user]),
            data=self.data_fields
        )
        response = self.authorized_client2.get(reverse('follow_index'))
        records_count = len(response.context['page'])
        self.assertEqual(records_count, 1)
        response = self.authorized_client3.get(reverse('follow_index'))
        records_count = len(response.context['page'])
        self.assertEqual(records_count, 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Nikolai')
        cls.group = Group.objects.create(title='reader',
                                         slug='test',
                                         description='Тест')
        for i in range(13):
            cls.post = Post.objects.create(
                text=f'Текст поста{i}',
                author=cls.user,
                group=cls.group
            )

    def check_paginator(self, response, records):
        posts = len(response.context.get('page').object_list)
        self.assertEqual(posts, records)

    def test_page_contains_actual_count_records(self):
        cache.clear()
        adresses = [
            reverse('index'),
            reverse('profile', args=[self.user])
        ]
        for adress in adresses:
            with self.subTest(adress=adress):
                response = self.client.get(adress)
                posts = len(response.context.get('page').object_list)
                self.assertEqual(posts, 10)
                response = self.client.get(adress + '?page=2')
                posts = len(response.context.get('page').object_list)
                self.assertEqual(posts, 3)
