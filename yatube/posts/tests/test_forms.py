import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='Nikolai')
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
            text='Старый текст',
            author=cls.user,
            group=cls.group
        )
        cls.form_data = {
            'text': 'Новый текст',
            'group': cls.group.id,
            'image': cls.uploaded
        }
        cls.comment = {
            'text': 'Комментарий добавлен'
        }
        cls.comment2 = {
            'text': 'Комментарий добавлен гостем'
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_new_post(self):
        """Валидная форма создает запись в Post и проверка Cache"""
        post_count = Post.objects.count()
        cache_index = cache.set("index_page", Post.objects.count())
        response = self.authorized_client.post(
            reverse('new_post'),
            data=self.form_data,
            follow=True
        )
        cache_index = cache.get("index_page")
        self.assertRedirects(response, reverse('index'))
        self.assertNotEqual(Post.objects.count(), cache_index)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.form_data['text'],
                author=User.objects.get(username='Nikolai'),
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        self.authorized_client.post(
            reverse('post_edit', args=[self.user, self.post.id]),
            data={'text': 'Новый текст', 'group': self.group.id}
        )
        posts = Post.objects.filter(author=self.user)
        for post in posts:
            self.assertEqual(post.text, 'Новый текст')

    def test_comment_for_authorized_client(self):
        """Только авторизированный пользователь может комментировать посты."""
        self.authorized_client.post(
            reverse('add_comment', args=[self.user, self.post.id]),
            data=self.comment
        )
        response = self.authorized_client.get(
            reverse('post', args=[self.user, self.post.id])
        )
        first_objects = response.context['post']
        comment_count = first_objects.comments.count()
        self.assertEqual(comment_count, 1)

    def test_comment_for_guest_client(self):
        """Гость не может комментировать посты."""
        self.guest_client.post(
            reverse('add_comment', args=[self.user, self.post.id]),
            data=self.comment2
        )
        response = self.authorized_client.get(
            reverse('post', args=[self.user, self.post.id])
        )
        first_objects = response.context['post']
        comment_count = first_objects.comments.count()
        self.assertEqual(comment_count, 0)
