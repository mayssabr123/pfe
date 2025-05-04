from accounts.models import Salle


def get_auto_salles():
    """
    Récupère toutes les salles en mode automatique (mode == 1).
    """
    auto_salles = Salle.objects.filter(mode=1)
    return [salle.name for salle in auto_salles]
