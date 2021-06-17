import rules

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates


# Allow listing templates and viewing details.
rules.add_perm(
    "containertemplates.view",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow creating templates.
rules.add_perm(
    "containertemplates.create",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)

# Allow updating templates.
rules.add_perm(
    "containertemplates.edit",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)

# Allow deleting templates.
rules.add_perm(
    "containertemplates.delete",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)
