def note_model(item):
    return {
        'id': str(item.get('_id', '')) if item.get('_id') else None,
        'doc_id': item.get('doc_id', None),
        'user_id': item.get('user_id', None),
        'type' : item.get('type', None),
        'title': item.get('title', None),
        'note': item.get('note', None),
        'date': item.get('date', None),
        'space': item.get('space', None)
    }


def note_models(items):
    return [note_model(item) for item in items]