from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .social_profiles import apply_social_profile


class HangarinSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        apply_social_profile(user, sociallogin.account.extra_data, persist=True)
        return user

    def pre_social_login(self, request, sociallogin):
        super().pre_social_login(request, sociallogin)
        if sociallogin.is_existing:
            apply_social_profile(sociallogin.user, sociallogin.account.extra_data, persist=True)
