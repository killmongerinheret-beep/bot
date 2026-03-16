# Multi-Tenant Telegram Bot Implementation Guide

## Overview
Allow your bot to be added to multiple groups/chats, with admin approval required before groups can receive notifications.

## Architecture

```
┌─────────────────────────────────────────┐
│         Telegram Groups/Chats           │
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │Group1│  │Group2│  │Group3│          │
│  └───┬──┘  └───┬──┘  └───┬──┘          │
└──────┼─────────┼─────────┼──────────────┘
       │         │         │
       └─────────┼─────────┘
                 │
         ┌───────▼────────┐
         │  Telegram Bot  │
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐  ┌────▼────┐  ┌───▼───┐
│Pending│  │Approved │  │Rejected│
│Groups │  │ Groups  │  │ Groups │
└───────┘  └────┬────┘  └────────┘
                │
         ┌──────▼──────┐
         │ Notifications│
         └─────────────┘
```

## Database Changes

### 1. Add TelegramGroup Model
```python
# backend/monitors/models.py

class TelegramGroup(models.Model):
    """
    Represents a Telegram group/chat that has added the bot.
    Requires admin approval before receiving notifications.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    # Telegram Info
    chat_id = models.CharField(max_length=255, unique=True, db_index=True)
    chat_type = models.CharField(max_length=20)  # 'group', 'supergroup', 'channel', 'private'
    chat_title = models.CharField(max_length=255, null=True, blank=True)
    chat_username = models.CharField(max_length=255, null=True, blank=True)
    
    # Linked Agency (optional - for multi-agency support)
    agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True, related_name='telegram_groups')
    
    # Approval Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.CharField(max_length=255, null=True, blank=True)  # Admin user ID
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    # Metadata
    added_by_user_id = models.CharField(max_length=255, null=True, blank=True)
    added_by_username = models.CharField(max_length=255, null=True, blank=True)
    added_by_first_name = models.CharField(max_length=255, null=True, blank=True)
    member_count = models.IntegerField(null=True, blank=True)
    
    # Settings
    notification_enabled = models.BooleanField(default=True)
    notification_language = models.CharField(max_length=10, default='en')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_name = 'telegram_groups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.chat_title or self.chat_id} ({self.status})"
    
    def is_approved(self):
        return self.status == 'approved'
    
    def approve(self, admin_id):
        self.status = 'approved'
        self.approved_by = admin_id
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, admin_id, reason=None):
        self.status = 'rejected'
        self.approved_by = admin_id
        self.rejection_reason = reason
        self.save()
    
    def suspend(self, reason=None):
        self.status = 'suspended'
        self.rejection_reason = reason
        self.save()
```

### 2. Create Migration
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

## Bot Implementation

### 1. Update Telegram Bot to Handle Group Joins
```python
# backend/telegram_bot.py

from telegram import Update, ChatMemberUpdated
from telegram.ext import ChatMemberHandler

async def handle_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle bot being added/removed from groups.
    This is called when bot's status changes in a chat.
    """
    from asgiref.sync import sync_to_async
    
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    
    was_member, is_member = result
    chat = update.effective_chat
    user = update.effective_user
    
    # Bot was added to a group
    if not was_member and is_member:
        logger.info(f"Bot added to {chat.type}: {chat.title} (ID: {chat.id}) by {user.first_name}")
        
        # Create or update TelegramGroup record
        group, created = await sync_to_async(TelegramGroup.objects.get_or_create)(
            chat_id=str(chat.id),
            defaults={
                'chat_type': chat.type,
                'chat_title': chat.title,
                'chat_username': chat.username,
                'added_by_user_id': str(user.id),
                'added_by_username': user.username,
                'added_by_first_name': user.first_name,
                'status': 'pending',
                'last_activity': timezone.now()
            }
        )
        
        if created:
            # Send welcome message
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    f"👋 Hello! I'm the Vatican Monitor Bot.\n\n"
                    f"🔒 This group is now **pending approval**.\n\n"
                    f"An admin will review your request shortly.\n"
                    f"Once approved, you'll receive notifications when Vatican tickets become available!\n\n"
                    f"Added by: {user.first_name}\n"
                    f"Group ID: `{chat.id}`\n\n"
                    f"⏳ Please wait for approval..."
                ),
                parse_mode='Markdown'
            )
            
            # Notify admins about new group request
            await notify_admins_new_group(context, group, user)
        else:
            # Group already exists
            if group.status == 'approved':
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"👋 Welcome back! This group is already approved.\n\n"
                        f"You'll receive notifications when Vatican tickets become available!"
                    )
                )
            elif group.status == 'pending':
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"⏳ This group is still pending approval.\n\n"
                        f"Please wait for an admin to review your request."
                    )
                )
            elif group.status == 'rejected':
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"❌ This group was previously rejected.\n\n"
                        f"Reason: {group.rejection_reason or 'Not specified'}\n\n"
                        f"Please contact support if you believe this is an error."
                    )
                )
    
    # Bot was removed from a group
    elif was_member and not is_member:
        logger.info(f"Bot removed from {chat.type}: {chat.title} (ID: {chat.id})")
        
        # Update group status
        group = await sync_to_async(TelegramGroup.objects.filter(chat_id=str(chat.id)).first)()
        if group:
            group.status = 'suspended'
            group.last_activity = timezone.now()
            await sync_to_async(group.save)()


def extract_status_change(chat_member_update: ChatMemberUpdated):
    """
    Extract whether the bot was added or removed from a chat.
    Returns (was_member, is_member) tuple or None if no change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))
    
    if status_change is None:
        return None
    
    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    
    return was_member, is_member


async def notify_admins_new_group(context, group, added_by_user):
    """
    Notify admin users about new group approval request.
    """
    from asgiref.sync import sync_to_async
    
    # Get admin chat IDs (you can store these in settings or database)
    ADMIN_CHAT_IDS = os.getenv('ADMIN_TELEGRAM_IDS', '').split(',')
    
    message = (
        f"🔔 **New Group Approval Request**\n\n"
        f"**Group:** {group.chat_title or 'Unnamed'}\n"
        f"**Type:** {group.chat_type}\n"
        f"**Chat ID:** `{group.chat_id}`\n"
        f"**Added by:** {added_by_user.first_name} (@{added_by_user.username or 'N/A'})\n"
        f"**User ID:** `{added_by_user.id}`\n"
        f"**Time:** {group.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Use the admin dashboard to approve or reject this group."
    )
    
    for admin_id in ADMIN_CHAT_IDS:
        if admin_id.strip():
            try:
                await context.bot.send_message(
                    chat_id=admin_id.strip(),
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")


# Add handler to main()
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ... existing handlers ...
    
    # Add chat member handler
    application.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
```

### 2. Update Notification Logic
```python
# backend/monitors/notification_utils.py

def send_telegram_signal(chat_id, message):
    """
    Send Telegram notification.
    Now checks if group is approved before sending.
    """
    from monitors.models import TelegramGroup
    
    # Check if this is a group and if it's approved
    try:
        group = TelegramGroup.objects.filter(chat_id=str(chat_id)).first()
        
        if group:
            if not group.is_approved():
                logger.warning(f"Skipping notification to unapproved group: {chat_id}")
                return False
            
            if not group.notification_enabled:
                logger.info(f"Notifications disabled for group: {chat_id}")
                return False
    except Exception as e:
        logger.error(f"Error checking group approval: {e}")
    
    # Send notification (existing logic)
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            # Update last_activity
            if group:
                group.last_activity = timezone.now()
                group.save(update_fields=['last_activity'])
            return True
        else:
            logger.error(f"Telegram API error: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
```

## Admin Dashboard

### 1. Backend API
```python
# backend/monitors/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_telegram_groups(request):
    """
    List all Telegram groups with their approval status.
    Admin only.
    """
    status_filter = request.query_params.get('status', None)
    
    groups = TelegramGroup.objects.all()
    
    if status_filter:
        groups = groups.filter(status=status_filter)
    
    groups = groups.order_by('-created_at')
    
    data = []
    for group in groups:
        data.append({
            'id': group.id,
            'chat_id': group.chat_id,
            'chat_title': group.chat_title,
            'chat_type': group.chat_type,
            'chat_username': group.chat_username,
            'status': group.status,
            'agency': {
                'id': group.agency.id,
                'name': group.agency.name
            } if group.agency else None,
            'added_by': {
                'user_id': group.added_by_user_id,
                'username': group.added_by_username,
                'first_name': group.added_by_first_name
            },
            'member_count': group.member_count,
            'notification_enabled': group.notification_enabled,
            'created_at': group.created_at,
            'approved_at': group.approved_at,
            'approved_by': group.approved_by,
            'rejection_reason': group.rejection_reason,
            'last_activity': group.last_activity
        })
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_telegram_group(request, group_id):
    """
    Approve a Telegram group.
    Admin only.
    """
    try:
        group = TelegramGroup.objects.get(id=group_id)
        agency_id = request.data.get('agency_id')
        
        # Link to agency if provided
        if agency_id:
            agency = Agency.objects.get(id=agency_id)
            group.agency = agency
        
        # Approve
        group.approve(admin_id=request.user.id)
        
        # Send approval notification to group
        from telegram import Bot
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        
        try:
            bot.send_message(
                chat_id=group.chat_id,
                text=(
                    f"✅ **Group Approved!**\n\n"
                    f"Your group has been approved by an admin.\n\n"
                    f"You will now receive notifications when Vatican tickets become available!\n\n"
                    f"Use /start to manage your monitors."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")
        
        return Response({'success': True, 'message': 'Group approved'})
        
    except TelegramGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_telegram_group(request, group_id):
    """
    Reject a Telegram group.
    Admin only.
    """
    try:
        group = TelegramGroup.objects.get(id=group_id)
        reason = request.data.get('reason', 'Not specified')
        
        # Reject
        group.reject(admin_id=request.user.id, reason=reason)
        
        # Send rejection notification to group
        from telegram import Bot
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        
        try:
            bot.send_message(
                chat_id=group.chat_id,
                text=(
                    f"❌ **Group Rejected**\n\n"
                    f"Your group approval request has been rejected.\n\n"
                    f"**Reason:** {reason}\n\n"
                    f"Please contact support if you believe this is an error."
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send rejection notification: {e}")
        
        return Response({'success': True, 'message': 'Group rejected'})
        
    except TelegramGroup.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# Add to urls.py
urlpatterns = [
    # ... existing urls ...
    path('api/v1/telegram-groups/', list_telegram_groups, name='list_telegram_groups'),
    path('api/v1/telegram-groups/<int:group_id>/approve/', approve_telegram_group, name='approve_telegram_group'),
    path('api/v1/telegram-groups/<int:group_id>/reject/', reject_telegram_group, name='reject_telegram_group'),
]
```

### 2. Frontend Dashboard Component
```typescript
// frontend/src/app/admin/telegram-groups/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface TelegramGroup {
  id: number
  chat_id: string
  chat_title: string
  chat_type: string
  status: 'pending' | 'approved' | 'rejected' | 'suspended'
  added_by: {
    first_name: string
    username: string
  }
  created_at: string
  agency?: {
    id: number
    name: string
  }
}

export default function TelegramGroupsPage() {
  const [groups, setGroups] = useState<TelegramGroup[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchGroups()
  }, [filter])
  
  const fetchGroups = async () => {
    try {
      const params = filter !== 'all' ? `?status=${filter}` : ''
      const response = await fetch(`/api/v1/telegram-groups/${params}`)
      const data = await response.json()
      setGroups(data)
    } catch (error) {
      console.error('Failed to fetch groups:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleApprove = async (groupId: number) => {
    if (!confirm('Approve this group?')) return
    
    try {
      await fetch(`/api/v1/telegram-groups/${groupId}/approve/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      fetchGroups()
    } catch (error) {
      console.error('Failed to approve group:', error)
      alert('Failed to approve group')
    }
  }
  
  const handleReject = async (groupId: number) => {
    const reason = prompt('Rejection reason:')
    if (!reason) return
    
    try {
      await fetch(`/api/v1/telegram-groups/${groupId}/reject/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      })
      fetchGroups()
    } catch (error) {
      console.error('Failed to reject group:', error)
      alert('Failed to reject group')
    }
  }
  
  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
      approved: 'bg-green-500/10 text-green-500 border-green-500/20',
      rejected: 'bg-red-500/10 text-red-500 border-red-500/20',
      suspended: 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    }
    return styles[status] || styles.pending
  }
  
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-8">
        Telegram Groups Management
      </h1>
      
      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        {['all', 'pending', 'approved', 'rejected'].map(status => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === status
                ? 'bg-[#00E37C] text-black'
                : 'bg-[#1a1a1a] text-[#888888] hover:text-white'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            {status !== 'all' && (
              <span className="ml-2 px-2 py-0.5 bg-black/20 rounded-full text-xs">
                {groups.filter(g => g.status === status).length}
              </span>
            )}
          </button>
        ))}
      </div>
      
      {/* Groups Table */}
      <div className="bg-[#0F0F0F] border border-[#262626] rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#1a1a1a]">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#888888]">Group</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#888888]">Type</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#888888]">Added By</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#888888]">Agency</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#888888]">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#888888]">Date</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#888888]">Actions</th>
            </tr>
          </thead>
          <tbody>
            {groups.map(group => (
              <tr key={group.id} className="border-t border-[#262626]">
                <td className="px-4 py-3">
                  <div className="text-white font-medium">{group.chat_title || 'Unnamed'}</div>
                  <div className="text-xs text-[#888888] font-mono">{group.chat_id}</div>
                </td>
                <td className="px-4 py-3 text-[#888888]">{group.chat_type}</td>
                <td className="px-4 py-3">
                  <div className="text-white">{group.added_by.first_name}</div>
                  <div className="text-xs text-[#888888]">@{group.added_by.username || 'N/A'}</div>
                </td>
                <td className="px-4 py-3 text-[#888888]">
                  {group.agency ? group.agency.name : 'Not linked'}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs border ${getStatusBadge(group.status)}`}>
                    {group.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-[#888888] text-sm">
                  {new Date(group.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  {group.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(group.id)}
                        className="px-3 py-1 bg-green-500/20 text-green-500 rounded text-sm hover:bg-green-500/30"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(group.id)}
                        className="px-3 py-1 bg-red-500/20 text-red-500 rounded text-sm hover:bg-red-500/30"
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

## Testing

### 1. Test Bot in Group
```bash
# 1. Add bot to a Telegram group
# 2. Check database for new TelegramGroup record
python manage.py shell
>>> from monitors.models import TelegramGroup
>>> TelegramGroup.objects.all()

# 3. Check admin received notification
# 4. Approve group via dashboard
# 5. Verify group receives test notification
```

### 2. Test Notification Filtering
```python
# backend/test_group_notifications.py
from monitors.models import TelegramGroup
from monitors.notification_utils import send_telegram_signal

# Test approved group
approved_group = TelegramGroup.objects.filter(status='approved').first()
send_telegram_signal(approved_group.chat_id, "Test notification")

# Test pending group (should be blocked)
pending_group = TelegramGroup.objects.filter(status='pending').first()
send_telegram_signal(pending_group.chat_id, "This should not send")
```

## Summary

This implementation provides:
- ✅ Multi-tenant support (multiple groups)
- ✅ Admin approval required
- ✅ Group management dashboard
- ✅ Automatic group detection
- ✅ Notification filtering
- ✅ Agency linking
- ✅ Status tracking

Next steps:
1. Run migrations
2. Update telegram_bot.py
3. Add admin dashboard page
4. Test with real groups
