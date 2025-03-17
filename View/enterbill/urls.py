from django.urls import path, include
from .views import PaperBillView, PendingView, DraftView, UploadfileView

enterbillurls = []
paperbillurls = [
    path('enter-bill/paper-bill/', PaperBillView.as_view(), name='paper-bill-list-create'),
    path('enter-bill/paper-bill/<int:pk>/', PaperBillView.as_view(), name='paper-bill-detail'),
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