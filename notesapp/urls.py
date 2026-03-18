from django.urls import path
from . import views

app_name = 'notesapp'

urlpatterns = [
    path('', views.NoteListView.as_view(), name='list'),
    path('note/<int:pk>/', views.NoteDetailView.as_view(), name='detail'),
    path('note/add/', views.NoteCreateView.as_view(), name='add'),
    path('note/<int:pk>/edit/', views.NoteUpdateView.as_view(), name='edit'),
    path('note/<int:pk>/delete/', views.NoteDeleteView.as_view(), name='delete'),
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('note/<int:pk>/approve/', views.approve_note, name='approve'),
    path('note/<int:pk>/reject/', views.reject_note, name='reject'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('users/', views.AdminUserListView.as_view(), name='user_list'),
    path('user/<int:pk>/block/', views.block_user, name='block_user'),
    path('user/<int:pk>/unblock/', views.unblock_user, name='unblock_user'),
    path('user/<int:pk>/delete/', views.delete_user, name='delete_user'),
]
