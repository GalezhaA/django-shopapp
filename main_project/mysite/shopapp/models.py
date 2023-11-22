from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from django.utils.translation import gettext_lazy as _


def product_preview_directory_path(instance: 'Product', filename: str) -> str:
    return 'products/product_{pk}/preview/{filename}'.format(
        pk=instance.pk,
        filename=filename,
    )


class Product(models.Model):
    class Meta:
        ordering = ['name', 'price']
        verbose_name = _('product')
        verbose_name_plural = _('products')

    name = models.CharField(max_length=100, verbose_name=_('наименование'))
    description = models.TextField(null=False, blank=True, verbose_name=_('описание'))
    price = models.DecimalField(default=0, max_digits=8, decimal_places=2, verbose_name=_('стоимость'))
    discount = models.SmallIntegerField(default=0, verbose_name=_('скидка'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата создания'))
    archived = models.BooleanField(default=False, verbose_name=_('в архиве'))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='products', null=True, verbose_name=_('создано пользователем'))
    preview = models.ImageField(null=True, blank=True, upload_to=product_preview_directory_path, verbose_name=_('превью'))

    def __str__(self) -> str:
        return f'Product(pk={self.pk}, name={self.name!r})'


def product_images_directory_path(instance: 'ProductImage', filename: str) -> str:
    return 'products/product_{pk}/images/{filename}'.format(
        pk=instance.product.pk,
        filename=filename,
    )


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=product_images_directory_path)
    description = models.CharField(max_length=200, null=False, blank=True)



class Order(models.Model):
    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    delivery_address = models.TextField(null=False, blank=True, verbose_name=_('адрес доставки'))
    promocode = models.CharField(max_length=20, null=False, blank=True, verbose_name=_('промокод'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата создания'))
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders', null=True, verbose_name=_('пользователь'))
    products = models.ManyToManyField(Product, related_name='orders', verbose_name=_('продукты'))
    receipt = models.FileField(null=True, upload_to='orders/receipts/', verbose_name=_('чек'))

    def get_absolute_url(self):
        return reverse('shopapp:order_details', kwargs={'pk': self.pk})