

# Register your models here.
from django.contrib import admin

# Register your models here.
from .models import Payment,Order,OrderProduct


class OrderProduceInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ('payment','user','product','quantity','product_price','ordered')

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number','full_name','phone','email','city','order_total','is_ordered','tax','status','created_at']
    list_filter = ['status','is_ordered']
    search_fields = ['order_number','first_name','last_name','phone','email']
    list_per_page = 20
    inlines = [OrderProduceInline]




admin.site.register(Order,OrderAdmin)
admin.site.register(Payment)
admin.site.register(OrderProduct)
