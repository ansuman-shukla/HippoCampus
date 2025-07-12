from datetime import datetime

def userModel(item):
    # Get current datetime for defaults
    now = datetime.utcnow()
    
    # Calculate first day of current month for reset date
    monthly_reset_date = datetime(now.year, now.month, 1)
    
    return {
        'id': str(item['_id']),
        'email': item['email'],
        'role': item['role'],
        'created_at': item['created_at'],
        'last_sign_in_at': item['last_sign_in_at'],
        'full_name': item['full_name'],
        'picture': item['picture'],
        'issuer': item['issuer'],
        'provider': item['provider'],
        'providers': item['providers'],
        
        # Subscription fields with defaults
        'subscription_tier': item.get('subscription_tier', 'free'),
        'subscription_status': item.get('subscription_status', 'active'),
        'subscription_start_date': item.get('subscription_start_date', now),
        'subscription_end_date': item.get('subscription_end_date', None),
        'total_memories_saved': item.get('total_memories_saved', 0),
        'monthly_summary_pages_used': item.get('monthly_summary_pages_used', 0),
        'monthly_summary_reset_date': item.get('monthly_summary_reset_date', monthly_reset_date)
    }

def userModels(items):
    return [userModel(item) for item in items]