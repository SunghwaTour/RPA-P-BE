from django.contrib import admin
from .models import Estimate, EstimateAddress, Pay, VirtualEstimate, EstimateTime
# Register your models here.
admin.site.register(EstimateTime)
admin.site.register(Estimate)
admin.site.register(EstimateAddress)
admin.site.register(VirtualEstimate)
admin.site.register(Pay)

