# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import TemplateView
from .models import Contact
from .forms import ContactForm

class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_form'] = ContactForm()
        return context

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            
            # Send email notification (optional)
            try:
                send_mail(
                    f'New Contact Inquiry: {contact.subject}',
                    f'''
                    New contact form submission:
                    
                    Name: {contact.name}
                    Email: {contact.email}
                    Phone: {contact.phone or "Not provided"}
                    Company: {contact.company or "Not provided"}
                    Subject: {contact.subject}
                    Message: {contact.message}
                    
                    Received: {contact.created_at}
                    ''',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],  # Add this to your settings
                    fail_silently=True,
                )
            except Exception as e:
                # Log the error but don't show to user
                print(f"Email sending failed: {e}")
            
            # Success message
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('index')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'core/index.html', {'contact_form': form})