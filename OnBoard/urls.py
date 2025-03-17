from .Company.urls import companyurls
from .Organization.urls import orgurls
from .Location.urls import locationurls
from .Ban.urls import banurlpatterns
# from .Ban.urls import banurlpatterns
urlpatterns = []

urlpatterns.extend(companyurls)
urlpatterns.extend(orgurls)
urlpatterns.extend(locationurls)
urlpatterns.extend(banurlpatterns)
