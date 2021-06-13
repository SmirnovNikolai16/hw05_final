from django.test import TestCase

from ..models import Group, Post, User


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mark')
        cls.group = Group.objects.create(title='reader',
                                         slug='test',
                                         description='Тест')
        cls.post = Post.objects.create(
            text='Xa' * 200,
            author=cls.user,
            group=cls.group
        )

    def test_object_name_is_title_group(self):
        """__str__  group - это строчка с содержимым group.title."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_object_name_is_text_post(self):
        """
        __str__  text - это строчка с содержимым post.text
         не более 15 символов.
        """
        post = ModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
