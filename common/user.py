def is_annotater(user):
    return user.groups.filter(name='annotater').exists()
