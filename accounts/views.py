from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegisterForm, EmailAuthenticationForm, ProfileForm
from .models import Profile
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


# -------------------------------------------------------------------
# LOGIN VIEW — safe (no duplicate email crash)
# -------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('inventory:dashboard')

    form = EmailAuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data.get('username')  # normalized email
            password = form.cleaned_data.get('password')

            # ✅ Always authenticate via username=email (safe & unique)
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                nxt = request.GET.get('next')
                return redirect(nxt or 'inventory:dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'accounts/login.html', {'form': form})


# -------------------------------------------------------------------
# REGISTER VIEW
# -------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect('inventory:dashboard')

    # Include request.FILES for file uploads
    form = RegisterForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Registration successful. Please log in.')
        return redirect('accounts:login')

    return render(request, 'accounts/register.html', {'form': form})


# -------------------------------------------------------------------
# PROFILE (VIEW & EDIT)
# -------------------------------------------------------------------
@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name() or request.user.email or request.user.username,
            "phone": "",
            "address": "",
            "medical_license": "",
        },
    )
    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name() or request.user.email or request.user.username,
            "phone": "",
            "address": "",
            "medical_license": "",
        },
    )

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})


# -------------------------------------------------------------------
# LOGOUT VIEW
# -------------------------------------------------------------------
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


# -------------------------------------------------------------------
# PASSWORD CHANGE (AJAX)
# -------------------------------------------------------------------
@require_POST
@login_required
def password_change_ajax(request):
    """Validate old password + new passwords using Django's PasswordChangeForm."""
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)
