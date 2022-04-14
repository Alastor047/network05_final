from http import HTTPStatus
import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание группы растянутое на много знаков',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='AnotherMan')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_existing_slug(self):
        """Проверка создания/наличия поста"""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Текст из формы',
            'image': self.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1, 'Не верно!')
        self.assertTrue(
            Post.objects.filter(text='Текст из формы').exists()
        )
        self.assertEqual(response.status_code, 200)

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_comment_on_page(self):
        """Комментарий появился на старнице поста"""
        post = self.post
        form_data = {
            'text': 'Тестовый коммент',
            post: post,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Comment.objects.filter(text='Тестовый коммент').exists())
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_comments_authorized_only(self):
        """Комментарии не доступны гостю"""
        post = self.post
        form_data = {
            'text': 'Тестовый коммент',
            post: post,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(text='Тестовый коммент').exists())
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id}))
