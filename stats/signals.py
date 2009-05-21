import django.dispatch

pot_has_changed = django.dispatch.Signal(providing_args=["potfile", "branch", "domain"])
