import logging

from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.urls import reverse_lazy, reverse as r
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Product, Order
from django.views import View
from django.contrib.auth.models import Group, User
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from .forms import OrderForm, GroupForm
from rest_framework.request import Request
from rest_framework.response import Response
from .serializers import ProductSerializer, OrdersSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

logger = logging.getLogger(__name__)


class UserOrdersExportView(View):
    def get(self, request: HttpRequest, **kwargs) -> JsonResponse:
        owner = get_object_or_404(User, pk=self.kwargs['user_id'])
        cache_name = f'user_orders_data_export_{owner.id}'
        serialized_data = cache.get(cache_name)

        if serialized_data is None:
            orders = Order.objects.filter(user=owner).order_by('pk').all()
            serialized = OrdersSerializer(orders, many=True)
            serialized_data = serialized.data
            cache.set(cache_name, serialized_data, 300)
            print('Делаем запрос в бд')

        return JsonResponse({'orders': serialized_data})


class UserOrdersListView(ListView):
    model = Order
    template_name = 'shopapp/user-orders.html'
    context_object_name = 'user_order'

    def get_queryset(self, **kwargs):
        owner = get_object_or_404(User, pk=self.kwargs['user_id'])
        orders = Order.objects.filter(user=owner)
        self.owner = owner
        queryset = {
            'user': owner,
            'orders': orders,
        }
        print('queryset', queryset)
        self.queryset = queryset
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        print('context', context)
        context['data'] = self.queryset
        print('context', context)
        print('context[data]', context['data'])
        return context


class LatestProductsFeed(Feed):
    title = 'Latest products'
    description = 'Updates shop products'
    link = reverse_lazy('shopapp:products_list')

    def items(self):
        return Order.objects.order_by('-created_at')[:5]

    def item_title(self, item: Order):
        return item.pk

    def item_description(self, item: Order):
        return item.products

    def item_link(self, item: Product):
        return reverse('shopapp:order_details', kwargs={'pk': item.pk})


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
    ]
    search_fields = ['name', 'description']
    filterset_fields = [
        'name',
        'description',
        'price',
        'discount',
        'archived'
    ]


class OrdersViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrdersSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        'delivery_address',
        'created_at',
        'promocode',
    ]
    filterset_fields = [
        'delivery_address',
        'created_at',
        'user',
        'promocode',
    ]


class ProductsApi(APIView):
    def get(self, request: Request) -> Response:
        products = Product.objects.all()
        serialized = ProductSerializer(products, many=True)
        return Response({'products': serialized.data})


class OrdersApi(APIView):
    def get(self, request: Request) -> Response:
        orders = Order.objects.all()
        serialized = OrdersSerializer(orders, many=True)
        return Response({'orders': serialized.data})


class ShopIndexView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ('Laptop', 1999),
            ('Desktop', 2999),
            ('Smartphone', 999)
        ]

        context = {
            'products': products
        }
        logger.debug('Product for shop index %s', products)
        logger.info('Rendering shop index')
        return render(request, 'shopapp/shop-index.html', context=context)


class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            'groups': Group.objects.prefetch_related('permissions').all(),
        }
        return render(request, 'shopapp/groups-list.html', context=context)

    def post(self, request: HttpRequest):
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect(request.path)


class OrdersListView(LoginRequiredMixin, ListView):
    queryset = (Order.objects
                .select_related('user')
                .prefetch_related('products'))


class OrderDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'shopapp.view_order'
    queryset = (Order.objects
                .select_related('user')
                .prefetch_related('products'))


class OrderUpdateView(UpdateView):
    model = Order
    fields = 'user', 'products'
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse(
            'shopapp:order_details',
            kwargs={'pk': self.object.pk}
        )


def create_order(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            url = reverse('shopapp:orders_list')
            return redirect(url)
    else:
        form = OrderForm()
        context = {
            'form': form,
        }

    return render(request, 'shopapp/create-order.html', context=context)


class OrderCreateView(CreateView):
    model = Order
    fields = 'user', 'products'
    success_url = reverse_lazy('shopapp:orders_list')


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy('shopapp:orders_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class ProductDetailsView(DetailView):
    template_name = 'shopapp/product-details.html'
    model = Product
    context_object_name = 'product'


class ProductsListView(ListView):
    template_name = 'shopapp/products-list.html'
    context_object_name = 'products'
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(PermissionRequiredMixin, CreateView):
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    permission_required = 'shopapp.add_product'
    model = Product
    fields = 'name', 'price', 'description', 'discount', 'preview'
    success_url = reverse_lazy('shopapp:products_list')


class ProductUpdateView(UserPassesTestMixin, UpdateView):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        self.object = self.get_object()
        has_edit_perm = self.request.user.has_perm("shopapp.change_product")
        created_by_current_user = self.object.created_by == self.request.user
        return has_edit_perm and created_by_current_user

    model = Product
    fields = 'name', 'price', 'description', 'discount', 'preview'
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse(
            'shopapp:product_details',
            kwargs={'pk': self.object.pk}
        )


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy('shopapp:products_list')

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        products = Product.objects.order_by('pk').all()
        products_data = [
            {
                'pk': product.pk,
                'name': product.name,
                'price': product.price,
                'archived': product.archived
            }
            for product in products
        ]
        elem = products_data[0]
        name = elem['name']
        print('name:', name)
        return JsonResponse({'products': products_data})


class OrdersDataExportView(UserPassesTestMixin, View):
    def test_func(self):
        if self.request.user.is_staff:
            return True
    def get(self, request: HttpRequest) -> JsonResponse:
        orders = Order.objects.order_by('pk').all()
        orders_data = [
            {
                'pk': order.pk,
                'address': order.delivery_address,
                'promocode': order.promocode,
                'user_is': str(order.user),
                'products': str(order.products.all())
            }
            for order in orders
        ]
        return JsonResponse({'orders': orders_data})


