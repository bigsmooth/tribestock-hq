def user_has_role(user, role_name: str) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=role_name).exists()

def is_admin(user): return user_has_role(user, "Admin") or user.is_superuser
def is_hub_manager(user): return user_has_role(user, "HubManager")
def is_retail(user): return user_has_role(user, "Retail")
def is_supplier(user): return user_has_role(user, "Supplier")
