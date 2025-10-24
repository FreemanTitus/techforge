from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_contact_reply_email(contact, reply_subject, reply_message, admin_name=None):
    """
    Send a professional reply email to a contact inquiry
    """
    context = {
        'contact_name': contact.name,
        'reply_message': reply_message,
        'original_subject': contact.subject,
        'original_message': contact.message,
        'original_date': contact.created_at.strftime('%B %d, %Y at %I:%M %p'),
        'admin_name': admin_name or 'Techforge Team',
        'company_name': 'Techforge Technologies',
    }
    
    # Render HTML and plain text versions
    html_content = render_to_string('emails/contact_reply.html', context)
    text_content = render_to_string('emails/contact_reply.txt', context)
    
    # Create email
    email = EmailMultiAlternatives(
        subject=reply_subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[contact.email],
        reply_to=[settings.REPLY_TO_EMAIL] if hasattr(settings, 'REPLY_TO_EMAIL') else None,
    )
    
    # Attach HTML version
    email.attach_alternative(html_content, "text/html")
    
    try:
        # Send email
        email.send(fail_silently=False)
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"