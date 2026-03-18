from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.utils.html import strip_tags
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from .models import Note, ContactMessage

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class AboutView(TemplateView):
    template_name = 'notesapp/about.html'

class ContactView(TemplateView):
    template_name = 'notesapp/contact.html'

    def post(self, request, *args, **kwargs):
        first_name = request.POST.get('first-name')
        last_name = request.POST.get('last-name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message_content = request.POST.get('message')

        if first_name and last_name and email and subject and message_content:
            # Save to database
            contact_msg = ContactMessage.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                subject=subject,
                message=message_content
            )

            # Send thank you email
            context = {
                'name': f"{first_name} {last_name}",
                'subject': subject,
                'support_email': settings.DEFAULT_FROM_EMAIL or 'support@notesapp.com',
                'dashboard_url': request.build_absolute_uri('/')
            }
            html_message = render_to_string('notesapp/emails/thank_you.html', context)
            plain_message = strip_tags(html_message)

            send_mail(
                subject='Thank You for Contacting NotesApp',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=True,
            )

            messages.success(request, 'Your message has been sent successfully! Check your email for confirmation.')
            return redirect('notesapp:contact')
        
        messages.error(request, 'Please fill in all the fields.')
        return self.get(request, *args, **kwargs)


class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'notesapp/note_list.html'
    context_object_name = 'notes'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            return queryset.filter(status='APPROVED')
        return queryset

class NoteDetailView(LoginRequiredMixin, DetailView):
    model = Note
    template_name = 'notesapp/note_detail.html'

class NoteCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Note
    fields = ['title', 'content', 'note_file']
    template_name = 'notesapp/note_form.html'
    success_url = reverse_lazy('notesapp:list')
    success_message = "Note submitted successfully! It is now pending admin approval."

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class NoteUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Note
    fields = ['title', 'content', 'note_file']
    template_name = 'notesapp/note_form.html'
    success_url = reverse_lazy('notesapp:list')
    success_message = "Note updated successfully!"

class NoteDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Note
    template_name = 'notesapp/note_confirm_delete.html'
    success_url = reverse_lazy('notesapp:list')
    success_message = "Note deleted successfully!"

class AdminDashboardView(UserPassesTestMixin, ListView):
    model = Note
    template_name = 'notesapp/admin_dashboard.html'
    context_object_name = 'recent_notes'
    
    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return Note.objects.all().order_by('-created_at')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_notes'] = Note.objects.count()
        context['total_users'] = User.objects.count()
        
        last_24h = timezone.now() - timedelta(hours=24)
        context['new_notes_24h'] = Note.objects.filter(created_at__gte=last_24h).count()
        context['pending_notes'] = Note.objects.filter(status='PENDING').count()
        
        context['all_users'] = User.objects.all().order_by('-date_joined')[:5]
        return context

@user_passes_test(lambda u: u.is_staff)
def approve_note(request, pk):
    note = Note.objects.get(pk=pk)
    note.status = 'APPROVED'
    note.save()
    
    if note.author and note.author.email:
        context = {
            'username': note.author.username,
            'note_title': note.title,
            'dashboard_url': request.build_absolute_uri('/'),
        }
        html_message = render_to_string('notesapp/emails/note_approved.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Your Note has been Approved!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[note.author.email],
            html_message=html_message,
            fail_silently=True,
        )
        
    return redirect('notesapp:dashboard')

@user_passes_test(lambda u: u.is_staff)
def reject_note(request, pk):
    note = Note.objects.get(pk=pk)
    note.status = 'REJECTED'
    note.save()
    
    if note.author and note.author.email:
        context = {
            'username': note.author.username,
            'note_title': note.title,
            'dashboard_url': request.build_absolute_uri('/'),
        }
        html_message = render_to_string('notesapp/emails/note_rejected.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Your Note has been Rejected',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[note.author.email],
            html_message=html_message,
            fail_silently=True,
        )
        
    return redirect('notesapp:dashboard')

class AdminUserListView(UserPassesTestMixin, ListView):
    model = User
    template_name = 'notesapp/admin_user_list.html'
    context_object_name = 'users'
    
    def test_func(self):
        return self.request.user.is_staff
        
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')

@user_passes_test(lambda u: u.is_staff)
def block_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not user.is_staff:  # App Admins should not block themselves
        user.is_active = False
        user.save()
        messages.success(request, f"User '{user.username}' has been successfully blocked.")
    else:
        messages.error(request, "Cannot block an admin user.")
    return redirect('notesapp:user_list')

@user_passes_test(lambda u: u.is_staff)
def unblock_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    messages.success(request, f"User '{user.username}' has been successfully unblocked.")
    return redirect('notesapp:user_list')

@user_passes_test(lambda u: u.is_staff)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not user.is_staff:
        user.delete()
        messages.success(request, f"User '{user.username}' has been completely removed.")
    else:
        messages.error(request, "Cannot delete an admin user.")
    return redirect('notesapp:user_list')
