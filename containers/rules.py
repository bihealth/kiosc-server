import rules

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates


# Allow listing containers and viewing details.
rules.add_perm(
    "containers.view_container",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow creating containers
rules.add_perm(
    "containers.create_container",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)

# Allow updating containers
rules.add_perm(
    "containers.edit_container",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)

# Allow deleting containers
rules.add_perm(
    "containers.delete_container",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)

# Allow starting containers
rules.add_perm(
    "containers.start_container",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)

# Allow stopping containers
rules.add_perm(
    "containers.stop_container",
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)
