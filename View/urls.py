from django.urls import path, include
from .viewbill.urls import viewbill_urls
from .enterbill.urls import enterbillurls
from .viewContract.urls import viewcontract_urls
urlpatterns = []
urlpatterns.extend(viewbill_urls)
urlpatterns.extend(enterbillurls)
urlpatterns.extend(viewcontract_urls)
