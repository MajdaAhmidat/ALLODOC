def user_role(request):
    role = None
    user = request.user
    if user.is_authenticated:
        if hasattr(user, 'medecin'):
            role = 'medecin'
        elif hasattr(user, 'patient'):
            role = 'patient'
        elif hasattr(user, 'pharmacien'):
            role = 'pharmacien'
        elif hasattr(user, 'laboratoire'):
            role = 'laboratoire'
    return {'user_role': role} 