from .rules import apply_temperature_rules  # si tu l'as dans un fichier séparé

# Cas de test : température élevée
print("Test 1 : Température = 36")
apply_temperature_rules(36)

# Cas de test : température basse
print("Test 2 : Température = 28")
apply_temperature_rules(28)

# Cas de test : température neutre
print("Test 3 : Température = 32")
apply_temperature_rules(32)
