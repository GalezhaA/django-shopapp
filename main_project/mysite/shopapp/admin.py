from csv import DictReader

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import path

from .models import Product, Order, ProductImage
from .admin_mixins import ExportAsCSVMixin
from .forms import CSVImportForm
from io import TextIOWrapper


class OrderInline(admin.TabularInline):
    model = Product.orders.through


class ProductInline(admin.StackedInline):
    model = ProductImage

@admin.action(description="Archive products")
def mark_archived(modeladmin:admin.ModelAdmin, request:HttpRequest, queryset: QuerySet):
    queryset.update(archived=True)


@admin.action(description="Unarchive products")
def mark_unarchived(modeladmin:admin.ModelAdmin, request:HttpRequest, queryset: QuerySet):
    queryset.update(archived=False)


class ProductAdmin(admin.ModelAdmin, ExportAsCSVMixin):
    actions = [
        mark_archived,
        mark_unarchived,
        'export_csv',
    ]
    inlines = [
        OrderInline,
        ProductInline,
    ]
    list_display = 'pk', 'name', 'description_short', 'price', 'discount', 'archived'
    list_display_links = 'pk', 'name'
    ordering = 'pk',
    search_fields = 'name', 'description'
    fieldsets = [
        (None, {
            'fields': ('name', 'description'),
        }),
        ('Price options', {
            'fields': ('price', 'discount'),
            'classes': ('wide', 'collapse',),
        }),
        ('Price options', {
            'fields': ('preview', ),

        }),
        ('Extra options', {
            'fields': ('archived',),
            'classes': ('collapse',),
            'description': 'Extra options. Field "archived" is for soft delete'
        })
    ]

    def description_short(self, obj: Product) -> str:
        if len(obj.description) < 48:
            return obj.description
        return obj.description[:48] + '... '



admin.site.register(Product, ProductAdmin)


class ProductInline(admin.StackedInline):
    model = Order.products.through


class OrderAdmin(admin.ModelAdmin):
    change_list_template = 'shopapp/orders_changelist.html'

    inlines = [
        ProductInline
    ]
    list_display = 'delivery_address', 'promocode', 'created_at', 'user_verbose'

    def get_queryset(self, request):
        return Order.objects.select_related('user').prefetch_related('products')

    def user_verbose(self, obj: Order) -> str:
        return obj.user.first_name or obj.user.username

    def import_csv(self, request: HttpRequest) -> HttpResponse:
        if request.method=='GET':
            form = CSVImportForm()
            context = {
                'form': form
            }
            return render(request, 'admin/csv_form.html', context=context)

        form = CSVImportForm(request.POST, request.FILES)
        if not form.is_valid():
            context = {
                'form': form
            }
            return render(request, 'admin/csv_form.html', context=context, status=400)

        csv_file = TextIOWrapper(
            form.files['csv_file'].file,
            encoding=request.encoding,
        )

        reader = DictReader(csv_file)
        orders = [
            row for row in reader
        ]
        print('orders', orders)
        for row in orders:
            print('row', row)
            instance = Order.objects.create(
                delivery_address=row['delivery_address'],
                promocode=row['promocode'],
                user_id=row['user']
            )
            for prod in row['products'].split('.'):
                instance.products.add(prod)

            print('instance', instance)

        self.message_user(request, 'Orders from CSV was imported!')
        return redirect('..')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path('import-orders-csv/',
                 self.import_csv,
                 name='import_orders_csv',
            )
        ]
        return new_urls + urls

admin.site.register(Order, OrderAdmin)

