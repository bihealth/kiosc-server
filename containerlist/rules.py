import rules


# Predicates -------------------------------------------------------------


# None needed right now


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------

rules.add_perm(
    'containerlist.view', rules.is_superuser | rules.is_authenticated
)
