import rules


# Predicates -------------------------------------------------------------


# None needed right now


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------

rules.add_perm("kioscadmin.admin", rules.is_superuser)
