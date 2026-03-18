from django.urls import reverse_lazy, reverse
from django.views import generic
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.contrib import messages
from .forms import CustomUserSignUpForm
import random
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import CustomUser

class SignUpView(generic.CreateView):
    form_class = CustomUserSignUpForm
    template_name = 'accounts/signup.html'
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False # Disable user until OTP verification
        user.save()
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        self.request.session['signup_otp'] = otp
        self.request.session['signup_user_id'] = user.id
        
        # Send OTP via Email
        context = {
            'fullname': user.fullname,
            'otp': otp
        }
        html_message = render_to_string('accounts/emails/otp_email.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject='Your NotesApp Signup OTP',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        messages.info(self.request, 'An OTP has been sent to your email. Please verify to complete signup.')
        return redirect('accounts:verify_otp')

def verify_otp(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        session_otp = request.session.get('signup_otp')
        user_id = request.session.get('signup_user_id')
        
        if otp_input == session_otp and user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                user.is_active = True
                user.save()
                
                # Clear session
                if 'signup_otp' in request.session:
                    del request.session['signup_otp']
                if 'signup_user_id' in request.session:
                    del request.session['signup_user_id']
                
                messages.success(request, 'Your account has been verified successfully! You can now login.')
                return redirect('accounts:login')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found. Try signing up again.')
                return render(request, 'accounts/verify_otp.html', {'error': 'User not found. Try signing up again.'})
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(request, 'accounts/verify_otp.html', {'error': 'Invalid OTP. Please try again.'})
            
    # Handle GET request
    if 'signup_user_id' not in request.session:
        return redirect('accounts:signup')
        
    return render(request, 'accounts/verify_otp.html')

class UserLoginView(SuccessMessageMixin, auth_views.LoginView):
    template_name = 'accounts/login.html'
    success_message = "Welcome back! You have successfully logged in."

class UserLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session['reset_otp'] = otp
            request.session['reset_user_id'] = user.id
            
            context = {
                'fullname': user.fullname,
                'otp': otp
            }
            html_message = render_to_string('accounts/emails/password_reset_otp.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='Password Reset OTP - NotesApp',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.info(request, 'An OTP has been sent to your email for password reset.')
            return redirect('accounts:password_reset_verify')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
            
    return render(request, 'accounts/password_reset_request.html')

def password_reset_verify(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        session_otp = request.session.get('reset_otp')
        
        if otp_input == session_otp:
            request.session['otp_verified'] = True
            return redirect('accounts:password_reset_confirm')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            
    if 'reset_user_id' not in request.session:
        return redirect('accounts:password_reset_request')
        
    return render(request, 'accounts/password_reset_verify.html')

def password_reset_confirm(request):
    if not request.session.get('otp_verified'):
        return redirect('accounts:password_reset_request')
        
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password == confirm_password:
            user_id = request.session.get('reset_user_id')
            user = CustomUser.objects.get(id=user_id)
            user.set_password(password)
            user.save()
            
            # Clear session
            del request.session['reset_otp']
            del request.session['reset_user_id']
            del request.session['otp_verified']
            
            messages.success(request, 'Password has been reset successfully! You can now login.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Passwords do not match.')
            
    return render(request, 'accounts/password_reset_confirm.html')

