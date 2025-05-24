def userModel(item):
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
        'providers': item['providers']    
    }

def userModels(items):
    return [userModel(item) for item in items]