from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

from .models import Medicine, Transaction, Manufacturer
from .forms import MedicineForm, TransactionForm, ManufacturerForm


@login_required
def dashboard(request):
    q = request.GET.get('q', '').strip()
    meds = Medicine.objects.filter(owner=request.user)
    if q:
        meds = meds.filter(Q(name__icontains=q) | Q(medicine_id__icontains=q))

    today = timezone.localdate()
    expiring_limit = today + timedelta(days=30)
    expired_count = meds.filter(exp_date__lt=today).count()
    expiring_count = meds.filter(exp_date__gte=today, exp_date__lte=expiring_limit).count()
    ok_count = meds.filter(exp_date__gt=expiring_limit).count()

    return render(request, 'inventory/dashboard.html', {
        'meds': meds,
        'q': q,
        'expired_count': expired_count,
        'expiring_count': expiring_count,
        'ok_count': ok_count,
    })


@login_required
def medicines(request):
    q = request.GET.get('q', '').strip()
    meds = Medicine.objects.filter(owner=request.user)
    if q:
        meds = meds.filter(Q(name__icontains=q) | Q(medicine_id__icontains=q))
    return render(request, 'inventory/medicines.html', {'meds': meds, 'q': q})


@login_required
def medicine_detail_partial(request, pk):
    med = get_object_or_404(Medicine, pk=pk, owner=request.user)
    return render(request, 'inventory/_medicine_detail.html', {'med': med})


@login_required
def records(request):
    """
    Add medicines, record Bought/Sold, search transactions.
    - Atomic stock updates
    - Robust validation/oversell checks
    - Unlimited search
    """
    # Bind forms (TransactionForm auto-scopes medicine queryset to request.user)
    if request.method == 'POST':
        mform = MedicineForm(request.POST) if 'save_medicine' in request.POST else MedicineForm()
        tform = TransactionForm(request.POST, user=request.user) if 'save_txn' in request.POST else TransactionForm(user=request.user)
    else:
        mform = MedicineForm()
        tform = TransactionForm(user=request.user)

    # Search query for transactions table (unlimited)
    q = (request.GET.get('q') or '').strip()

    if request.method == 'POST':
        if 'save_medicine' in request.POST:
            if mform.is_valid():
                obj = mform.save(commit=False)
                obj.owner = request.user
                # Safety: ensure quantity_on_hand default
                if getattr(obj, 'quantity_on_hand', None) is None:
                    obj.quantity_on_hand = 0
                obj.save()
                messages.success(request, 'Medicine saved successfully.')
                return redirect('inventory:records')
            else:
                messages.error(request, 'Please fix the medicine form errors.')

        elif 'save_txn' in request.POST:
            if tform.is_valid():
                txn = tform.save(commit=False)
                txn.owner = request.user
                med = txn.medicine

                oversell_error = False
                # Apply stock mutation in memory first
                if txn.ttype == 'BOUGHT':
                    new_qty = med.quantity_on_hand + txn.quantity
                else:  # SOLD
                    if txn.quantity > med.quantity_on_hand:
                        oversell_error = True
                        messages.error(
                            request,
                            f"Cannot sell {txn.quantity}. Only {med.quantity_on_hand} in stock."
                        )
                        new_qty = med.quantity_on_hand  # unchanged
                    else:
                        new_qty = med.quantity_on_hand - txn.quantity

                if not oversell_error:
                    # Commit both updates atomically
                    with transaction.atomic():
                        med.quantity_on_hand = new_qty
                        med.save(update_fields=['quantity_on_hand'])
                        txn.save()
                    messages.success(request, 'Transaction saved successfully.')
                    return redirect('inventory:records')
            else:
                messages.error(request, 'Please fix the transaction form errors.')

    # Build transactions list (no limit) + search (partner/medicine/date)
    txns = Transaction.objects.filter(owner=request.user).select_related('medicine').order_by('-created_at')
    if q:
        # Try to parse YYYY-MM-DD or DD/MM/YYYY and search exact date if possible
        date_filter = Q()
        dq = q
        try:
            # naive parse attempts
            from datetime import datetime
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    parsed = datetime.strptime(dq, fmt).date()
                    date_filter = Q(created_at__date=parsed)
                    break
                except ValueError:
                    continue
        except Exception:
            pass

        txns = txns.filter(
            Q(partner_name__icontains=q) |
            Q(medicine__name__icontains=q) |
            date_filter |
            Q(created_at__date__icontains=q)  # fallback: substring
        )

    return render(request, 'inventory/records.html', {
        'mform': mform,
        'tform': tform,
        'txns': txns,
        'q': q,
    })


@login_required
def manufacturers(request):
    if request.method == 'POST':
        form = ManufacturerForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            # If your Manufacturer model has owner, attach it; otherwise this no-ops
            if hasattr(obj, 'owner_id'):
                obj.owner = request.user
            obj.save()
            messages.success(request, 'Manufacturer saved.')
            return redirect('inventory:manufacturers')
    else:
        form = ManufacturerForm()

    q = request.GET.get('q', '').strip()

    items = Manufacturer.objects.all().order_by('name')
    # Scope to user if model supports it
    if hasattr(Manufacturer, 'owner'):
        items = items.filter(owner=request.user)

    if q:
        items = items.filter(
            Q(name__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(phone__icontains=q) |
            Q(address__icontains=q)
        )

    return render(request, 'inventory/manufacturers.html', {
        'form': form,
        'items': items,
        'q': q,
    })


@login_required
def medicine_edit_partial(request, pk):
    """Return the edit form as a partial to load inside the right pane."""
    med = get_object_or_404(Medicine, pk=pk, owner=request.user)
    form = MedicineForm(instance=med)
    html = render_to_string('inventory/_medicine_form.html', {'form': form, 'med': med}, request)
    return HttpResponse(html)


@login_required
@require_http_methods(["POST"])
def medicine_edit(request, pk):
    """Accept POST from the inline form; return updated detail partial or form with errors."""
    med = get_object_or_404(Medicine, pk=pk, owner=request.user)
    form = MedicineForm(request.POST, instance=med)
    if form.is_valid():
        form.save()
        messages.success(request, 'Medicine updated.')
        html = render_to_string('inventory/_medicine_detail.html', {'med': med, 'saved': True}, request)
        return HttpResponse(html)
    # Return the form again (with errors)
    html = render_to_string('inventory/_medicine_form.html', {'form': form, 'med': med}, request)
    return HttpResponse(html, status=400)


@login_required
@require_http_methods(["POST"])
def medicine_delete(request, pk):
    """Delete medicine and redirect or return empty pane."""
    med = get_object_or_404(Medicine, pk=pk, owner=request.user)
    med.delete()
    messages.success(request, 'Medicine deleted.')

    # If it's an AJAX request, just refresh the right pane.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('inventory/_empty_detail.html', {}, request)
        return HttpResponse(html)

    # Otherwise redirect user to the dashboard.
    return redirect('inventory:dashboard')


@login_required
def medlist_partial(request):
    """Return just the list markup for the left list (used after save/delete)."""
    q = request.GET.get('q', '').strip()
    meds = Medicine.objects.filter(owner=request.user)
    if q:
        meds = meds.filter(Q(name__icontains=q) | Q(medicine_id__icontains=q))
    html = render_to_string('inventory/_med_list.html', {'meds': meds}, request)
    return HttpResponse(html)
