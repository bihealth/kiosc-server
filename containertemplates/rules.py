import rules


# Allow listing templates and viewing details.
rules.add_perm(
    "containertemplates.view",
    rules.is_superuser | rules.is_authenticated,
)

# Allow creating templates.
rules.add_perm(
    "containertemplates.create",
    rules.is_superuser,
)

# Allow updating templates.
rules.add_perm(
    "containertemplates.edit",
    rules.is_superuser,
)

# Allow deleting templates.
rules.add_perm(
    "containertemplates.delete",
    rules.is_superuser,
)

# Allow duplicating templates.
rules.add_perm(
    "containertemplates.duplicate",
    rules.is_superuser,
)
