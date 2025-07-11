from django.urls import path, include
from .views import UploadedBillView, PendingView, DraftView, UploadfileView

enterbillurls = []
paperbillurls = [
    path('enter-bill/uploaded-bill/', UploadedBillView.as_view(), name='paper-bill-list-create'),
    path('enter-bill/uploaded-bill/<int:pk>/', UploadedBillView.as_view(), name='paper-bill-detail'),
]


enterbillurls.extend(paperbillurls)


pendingurls = [
    path('enter-bill/pending-bill/', PendingView.as_view(), name='pending-bill-list-create'),
    path('enter-bill/pending-bill/<int:pk>/', PendingView.as_view(), name='pending-bill-detail'),
]

enterbillurls.extend(pendingurls)

drafturls = [
    path('enter-bill/draft-bill/', DraftView.as_view(), name='draft-bill-list-create'),
    path('enter-bill/draft-bill/<int:pk>/', DraftView.as_view(), name='draft-bill-detail'),
]


enterbillurls.extend(drafturls)

uploadfileurls = [
    path('enter-bill/upload-file/', UploadfileView.as_view(), name='upload-file'),
    path('enter-bill/upload-file/<int:pk>/', UploadfileView.as_view(), name='upload-file-detail'),
]

enterbillurls.extend(uploadfileurls)

from .views import ApproveView, AprroveAllView, AddNoteView
approveurls = [
    path('approve-bill/<int:id>/', ApproveView.as_view(), name='approve-bill'),
    path('approve-all/<int:id>/', AprroveAllView.as_view(), name='approve-all'),
    path('add-baseline-notes/', AddNoteView.as_view(), name='add-note'),
]
enterbillurls.extend(approveurls)

from .views import PaperBillView

paperbillurls = [
    path('enter-bill/paper-bill/', PaperBillView.as_view(), name='paper-bill')
]

enterbillurls.extend(paperbillurls)