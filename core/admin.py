from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Contact
from .utils import send_contact_reply_email

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at', 'reply_action']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'contact_details', 'reply_preview']
    list_editable = ['status']
    fieldsets = (
        ('Contact Information', {
            'fields': ('contact_details',)
        }),
        ('Message Details', {
            'fields': ('subject', 'message')
        }),
        ('Reply', {
            'fields': ('reply_subject', 'reply_message', 'reply_preview', 'admin_notes')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    def contact_details(self, obj):
        return format_html(
            """
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p><strong>Name:</strong> {}</p>
                <p><strong>Email:</strong> {}</p>
                <p><strong>Phone:</strong> {}</p>
                <p><strong>Company:</strong> {}</p>
            </div>
            """,
            obj.name,
            obj.email,
            obj.phone or "Not provided",
            obj.company or "Not provided"
        )
    contact_details.short_description = "Contact Details"
    
    def reply_preview(self, obj):
        if not obj.reply_subject or not obj.reply_message:
            return "No reply drafted yet"
        
        return format_html(
            """
            <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2563eb; margin: 10px 0;">
                <h4 style="margin-top: 0; color: #1e40af;">Preview:</h4>
                <p><strong>Subject:</strong> {}</p>
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    {}
                </div>
            </div>
            """,
            obj.reply_subject,
            obj.reply_message.replace('\n', '<br>')
        )
    reply_preview.short_description = "Reply Preview"
    
    def reply_action(self, obj):
        return format_html(
            '<a class="button" href="{}">Reply</a>',
            f'{obj.id}/reply/'
        )
    reply_action.short_description = 'Action'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/reply/', self.admin_site.admin_view(self.reply_view), name='core_contact_reply'),
        ]
        return custom_urls + urls
    
    def reply_view(self, request, object_id):
        contact = Contact.objects.get(id=object_id)
        
        if request.method == 'POST':
            reply_subject = request.POST.get('reply_subject', '')
            reply_message = request.POST.get('reply_message', '')
            admin_notes = request.POST.get('admin_notes', '')
            send_email = 'send_email' in request.POST
            
            if reply_subject and reply_message:
                # Save draft to contact record
                contact.reply_subject = reply_subject
                contact.reply_message = reply_message
                contact.admin_notes = admin_notes
                
                if send_email:
                    # Send email using template
                    success, message = send_contact_reply_email(
                        contact=contact,
                        reply_subject=reply_subject,
                        reply_message=reply_message
                    )
                    
                    if success:
                        contact.status = 'replied'
                        contact.save()
                        messages.success(request, f'Reply sent successfully to {contact.email}')
                        return HttpResponseRedirect('../../')
                    else:
                        messages.error(request, message)
                else:
                    # Just save as draft
                    contact.save()
                    messages.success(request, 'Reply saved as draft')
                    return HttpResponseRedirect('../../')
            else:
                messages.error(request, 'Both subject and message are required.')
        
        # Pre-fill default values
        default_subject = f"Re: {contact.subject}"
        default_message = f"""Dear {contact.name},

Thank you for contacting Techforge Technologies. We have received your inquiry regarding "{contact.subject}".

"""

        context = {
            **self.admin_site.each_context(request),
            'contact': contact,
            'opts': self.model._meta,
            'default_subject': default_subject,
            'default_message': default_message,
            'title': f'Reply to {contact.name}',
        }
        
        return render(request, 'core/contact_reply.html', context)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return list(self.readonly_fields) + ['contact_details', 'reply_preview']
        return self.readonly_fields