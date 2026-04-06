def _read_value(data, *keys):
    for key in keys:
        value = str(data.get(key, "")).strip()
        if value:
            return value
    return ""


def extract_social_profile(data):
    first_name = _read_value(data, "first_name", "given_name")
    last_name = _read_value(data, "last_name", "family_name")
    full_name = _read_value(data, "name")
    username = _read_value(data, "preferred_username", "login", "username")
    email = _read_value(data, "email")

    if not full_name:
        full_name = " ".join(part for part in [first_name, last_name] if part).strip()

    if full_name and not first_name:
        first_name = full_name.split(" ", 1)[0]

    if full_name and not last_name and " " in full_name:
        last_name = full_name.split(" ", 1)[1].strip()

    return {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "username": username,
        "email": email,
    }


def apply_social_profile(user, data, *, persist=False):
    if not user or not data:
        return []

    profile = extract_social_profile(data)
    update_fields = []

    if profile["first_name"] and user.first_name != profile["first_name"]:
        user.first_name = profile["first_name"]
        update_fields.append("first_name")

    if profile["last_name"] and user.last_name != profile["last_name"]:
        user.last_name = profile["last_name"]
        update_fields.append("last_name")

    if profile["email"] and not user.email:
        user.email = profile["email"]
        update_fields.append("email")

    if persist and update_fields:
        user.save(update_fields=update_fields)

    return update_fields


def get_user_social_data(user):
    if not user or not getattr(user, "is_authenticated", False):
        return {}

    social_accounts = getattr(user, "socialaccount_set", None)
    if social_accounts is None:
        return {}

    social_account = social_accounts.order_by("-pk").first()
    if not social_account:
        return {}

    return social_account.extra_data or {}


def resolve_user_display_name(user):
    if not user or not getattr(user, "is_authenticated", False):
        return ""

    full_name = user.get_full_name().strip()
    if full_name:
        return full_name

    profile = extract_social_profile(get_user_social_data(user))
    if profile["full_name"]:
        return profile["full_name"]

    if profile["username"]:
        return profile["username"]

    if user.email:
        return user.email.split("@", 1)[0]

    return user.get_username()


def resolve_user_avatar_text(user):
    display_name = resolve_user_display_name(user)
    return display_name[:1].upper() if display_name else "?"
