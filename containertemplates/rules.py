import rules

from projectroles import rules as pr_rules


# Allow listing site-wide templates and viewing details.
rules.add_perm(
    "containertemplates.site_view",
    rules.is_superuser | rules.is_authenticated,
)

# Allow creating site-wide templates.
rules.add_perm(
    "containertemplates.site_create",
    rules.is_superuser,
)

# Allow updating site-wide templates.
rules.add_perm(
    "containertemplates.site_edit",
    rules.is_superuser,
)

# Allow deleting site-wide templates.
rules.add_perm(
    "containertemplates.site_delete",
    rules.is_superuser,
)

# Allow duplicating site-wide templates.
rules.add_perm(
    "containertemplates.site_duplicate",
    rules.is_superuser,
)

# Allow listing project-wide templates and viewing details.
rules.add_perm(
    "containertemplates.project_view",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow creating project-wide templates.
rules.add_perm(
    "containertemplates.project_create",
    pr_rules.can_modify_project_data
    & (
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
    ),
)

# Allow updating project-wide templates.
rules.add_perm(
    "containertemplates.project_edit",
    pr_rules.can_modify_project_data
    & (
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
    ),
)

# Allow deleting project-wide templates.
rules.add_perm(
    "containertemplates.project_delete",
    pr_rules.can_modify_project_data
    & (
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
    ),
)

# Allow duplicating project-wide templates.
rules.add_perm(
    "containertemplates.project_duplicate",
    pr_rules.can_modify_project_data
    & (
        pr_rules.is_project_owner
        | pr_rules.is_project_delegate
        | pr_rules.is_project_contributor
    ),
)
