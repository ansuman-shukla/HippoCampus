def bookmarkModel(item):
    return {
        'id': str(item.get('_id', '')) if item.get('_id') else None,
        'doc_id': item.get('doc_id', None),
        'user_id': item.get('user_id', None),
        'title': item.get('title', None),
        'type': item.get('type', None),
        'note': item.get('note', None),
        'source_url': item.get('source_url', None),
        'site_name': item.get('site_name', None),
        'date': item.get('date', None),
        'space': item.get('space', None)
    }

def bookmarkModels(items):
    return [bookmarkModel(item) for item in items]