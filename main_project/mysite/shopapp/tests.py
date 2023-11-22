from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from string import ascii_letters
from random import choices
from django.conf import settings

from shopapp.models import Product, Order
from shopapp.utils import add_two_numbers

class AddTWoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_two_numbers(4, 3)
        self.assertEqual(result, 7)


class ProductCreateViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.credentials = dict(username="test_user", password="qwerty")
        cls.user = User.objects.create_user(**cls.credentials)
        permission = Permission.objects.get()
        cls.user.user_permissions.add(permission)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self):
        self.product_name = ''.join(choices(ascii_letters, k=10))
        Product.objects.filter(name=self.product_name).delete()
        self.client.force_login(self.user)


    def test_create_product(self):
        response = self.client.post(
            reverse('shopapp:product_create'),
            {
                'name': self.product_name,
                'price': '123.45',
                'description': 'A good table',
                'discount': '10',
                'created_by': '2'

            },
            HTTP_USER_AGENT='Mozilla/5.0'
        )
        self.assertRedirects(response, reverse('shopapp:products_list'))
        self.assertTrue(
            Product.objects.filter(name=self.product_name).exists()
        )


class ProductsListViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json',
    ]

    def test_products(self):
        response = self.client.get(reverse('shopapp:products_list'))

        self.assertQuerysetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=(p.pk for p in response.context['products']),
            transform=lambda p: p.pk,
        )
        self.assertTemplateUsed(response, 'shopapp/products-list.html')


class OrdersListViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='bob_test', password='qwerty')

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self):
        self.client.force_login(self.user)

    def test_orders_view(self):
        response = self.client.get(reverse('shopapp:orders_list'))
        self.assertContains(response, 'Orders')

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse('shopapp:orders_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)


class ProductDetailsViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.product = Product.objects.create(name='Best product')

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()

    def test_get_product(self):
        response = self.client.get(reverse('shopapp:product_details', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)

    def test_get_product_and_check_content(self):
        response = self.client.get(reverse('shopapp:product_details', kwargs={'pk': self.product.pk}))
        self.assertContains(response, self.product.name)


class ProductsExportViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json',
    ]

    def test_get_products_view(self):
        response = self.client.get(reverse('shopapp:products-export'))
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by('pk').all()
        expected_data = [
            {
                'pk': product.pk,
                'name': product.name,
                'price': str(product.price),
                'archived': product.archived,
            }
            for product in products
        ]
        products_data = response.json()
        self.assertEqual(
            products_data['products'],
            expected_data
        )


class OrderDetailViewTestCase(PermissionRequiredMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            username='tom_test',
            password='qwerty123',
        )
        permission_required = ['shopapp.view_order']


    @classmethod
    def tearDownClass(cls):
        cls.user.delete()


    def setUp(self):
        self.client.force_login(self.user)
        self.order = Order.objects.create()


    def tearDown(self):
        self.order.delete()

    def test_order_details(self):
        response = self.client.post(
            reverse('shopapp:order_create'),
            {
                'delivery_address': 'my home',
                'promocode': 'SALE',
                'created_at': '',
                'user_id': '',
            },
            HTTP_USER_AGENT='Mozilla/5.0')
        self.assertContains(response, self.order.delivery_address)
        self.assertContains(response, self.order.promocode)
        self.assertContains(response, self.order.pk)


class OrdersExportTestCase(PermissionRequiredMixin, TestCase):
    fixtures = [
        'user-fixtures.json',
        'products-fixture.json',
        'orders-fixtures.json',
    ]
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_superuser(
            username='aboba',
            password='amogus',
        )

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self):
        self.client.force_login(self.user)

    def test_order_export_view(self):
        response = self.client.get(reverse('shopapp:orders-export'))
        self.assertEqual(response.status_code,200)
        orders = Order.objects.order_by('pk').all()
        expected_data = [
            {
                'pk': order.pk,
                'address': order.delivery_address,
                'promocode': order.promocode,
                'user_is': str(order.user),
                'products': str(order.products.all())
            }
            for order in orders
        ]
        orders_data = response.json()
        self.assertEqual(
            orders_data['orders'],
            expected_data
        )